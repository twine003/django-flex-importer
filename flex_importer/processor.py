"""
Import processor for FlexImporter
"""
import csv
import json
from io import TextIOWrapper, BytesIO
from openpyxl import load_workbook
from django.utils import timezone
from .models import ImportLog


class ImportProcessor:
    """Process imports from different file formats"""

    def __init__(self, import_log):
        self.import_log = import_log
        self.importer_class = None

    def process(self):
        """Main process method to handle import"""
        try:
            from .registry import importer_registry

            self.importer_class = importer_registry.get_importer(
                self.import_log.importer_class
            )

            if not self.importer_class:
                self.import_log.status = 'failed'
                self.import_log.result_message = 'Clase importadora no encontrada'
                self.import_log.save()
                return False

            self.import_log.status = 'processing'
            self.import_log.started_at = timezone.now()
            self.import_log.add_progress_log('Iniciando importación...')
            self.import_log.save()

            file_format = self.import_log.file_format
            file_path = self.import_log.uploaded_file.path

            if file_format == 'xlsx':
                rows = self._read_xlsx(file_path)
            elif file_format == 'csv':
                rows = self._read_csv(file_path)
            elif file_format == 'json':
                rows = self._read_json(file_path)
            else:
                raise ValueError(f'Formato no soportado: {file_format}')

            self.import_log.total_rows = len(rows)
            self.import_log.add_progress_log(f'Se encontraron {len(rows)} filas para procesar')
            self.import_log.save()

            self._process_rows(rows)

            self.import_log.completed_at = timezone.now()

            if self.import_log.error_rows == 0:
                self.import_log.status = 'success'
                message_parts = [f'Importación completada exitosamente. {self.import_log.success_rows} filas procesadas']
                if self.import_log.updated_rows > 0 or self.import_log.created_rows > 0:
                    message_parts.append(f'({self.import_log.created_rows} creadas, {self.import_log.updated_rows} actualizadas)')
                self.import_log.result_message = ' '.join(message_parts) + '.'
            elif self.import_log.success_rows > 0:
                self.import_log.status = 'partial'
                message_parts = [f'Importación parcial. {self.import_log.success_rows} exitosas']
                if self.import_log.updated_rows > 0 or self.import_log.created_rows > 0:
                    message_parts.append(f'({self.import_log.created_rows} creadas, {self.import_log.updated_rows} actualizadas)')
                message_parts.append(f'{self.import_log.error_rows} con errores')
                self.import_log.result_message = ', '.join(message_parts) + '.'
            else:
                self.import_log.status = 'failed'
                self.import_log.result_message = f'Importación fallida. Todas las filas tuvieron errores.'

            self.import_log.add_progress_log(self.import_log.result_message, 'success' if self.import_log.status == 'success' else 'warning')
            self.import_log.save()

            return True

        except Exception as e:
            self.import_log.status = 'failed'
            self.import_log.result_message = f'Error en importación: {str(e)}'
            self.import_log.completed_at = timezone.now()
            self.import_log.add_progress_log(f'Error: {str(e)}', 'error')
            self.import_log.save()
            return False

    def _read_xlsx(self, file_path):
        """Read data from Excel file"""
        wb = load_workbook(file_path, data_only=True)
        ws = wb.active

        headers = []
        for cell in ws[1]:
            if cell.value:
                header = str(cell.value).replace(' *', '').strip()
                headers.append(header)

        rows = []
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if all(cell is None or cell == '' for cell in row):
                continue

            row_data = {}
            for idx, value in enumerate(row):
                if idx < len(headers):
                    row_data[headers[idx]] = value

            row_data['_row_number'] = row_idx
            rows.append(row_data)

        return rows

    def _read_csv(self, file_path):
        """Read data from CSV file"""
        rows = []

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            headers = [h.replace(' *', '').strip() for h in reader.fieldnames]
            reader.fieldnames = headers

            for row_idx, row in enumerate(reader, start=2):
                if all(not value or value == '' for value in row.values()):
                    continue

                row['_row_number'] = row_idx
                rows.append(row)

        return rows

    def _read_json(self, file_path):
        """Read data from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, dict) and 'data' in data:
            rows = data['data']
        elif isinstance(data, list):
            rows = data
        else:
            raise ValueError('Formato JSON inválido. Debe ser una lista o un objeto con propiedad "data"')

        for idx, row in enumerate(rows, start=1):
            row['_row_number'] = idx

        return rows

    def _process_rows(self, rows):
        """Process each row of data"""
        field_info = self.importer_class.get_field_info()
        field_name_map = {info['verbose_name']: info['name'] for info in field_info}

        importer_instance = self.importer_class()

        for idx, row_data in enumerate(rows, start=1):
            row_number = row_data.get('_row_number', idx)

            normalized_data = {}
            for key, value in row_data.items():
                if key == '_row_number':
                    continue

                field_name = field_name_map.get(key, key)
                normalized_data[field_name] = value

            validated_data, errors = self.importer_class.validate_row(normalized_data)

            if errors:
                self.import_log.error_rows += 1
                error_entry = {
                    'row': row_number,
                    'errors': errors,
                    'data': normalized_data
                }
                if self.import_log.error_details is None:
                    self.import_log.error_details = []
                self.import_log.error_details.append(error_entry)
                self.import_log.add_progress_log(
                    f'Fila {row_number}: Errores de validación - {", ".join(errors)}',
                    'error'
                )
            else:
                try:
                    result = importer_instance.import_action(validated_data)

                    if result is True or result is None:
                        self.import_log.success_rows += 1
                        self.import_log.created_rows += 1
                        if idx % 10 == 0 or idx == len(rows):
                            self.import_log.add_progress_log(
                                f'Procesadas {idx} de {len(rows)} filas...',
                                'info'
                            )
                    elif isinstance(result, dict) and result.get('action') in ['created', 'updated']:
                        self.import_log.success_rows += 1
                        if result['action'] == 'created':
                            self.import_log.created_rows += 1
                        else:
                            self.import_log.updated_rows += 1

                        if idx % 10 == 0 or idx == len(rows):
                            self.import_log.add_progress_log(
                                f'Procesadas {idx} de {len(rows)} filas ({self.import_log.created_rows} creadas, {self.import_log.updated_rows} actualizadas)...',
                                'info'
                            )
                    else:
                        self.import_log.error_rows += 1
                        error_entry = {
                            'row': row_number,
                            'errors': [str(result)],
                            'data': normalized_data
                        }
                        if self.import_log.error_details is None:
                            self.import_log.error_details = []
                        self.import_log.error_details.append(error_entry)
                        self.import_log.add_progress_log(
                            f'Fila {row_number}: Error en import_action - {result}',
                            'error'
                        )

                except Exception as e:
                    self.import_log.error_rows += 1
                    error_entry = {
                        'row': row_number,
                        'errors': [f'Excepción: {str(e)}'],
                        'data': normalized_data
                    }
                    if self.import_log.error_details is None:
                        self.import_log.error_details = []
                    self.import_log.error_details.append(error_entry)
                    self.import_log.add_progress_log(
                        f'Fila {row_number}: Excepción - {str(e)}',
                        'error'
                    )

            self.import_log.processed_rows += 1
            self.import_log.save(update_fields=['processed_rows', 'success_rows', 'created_rows', 'updated_rows', 'error_rows', 'error_details'])

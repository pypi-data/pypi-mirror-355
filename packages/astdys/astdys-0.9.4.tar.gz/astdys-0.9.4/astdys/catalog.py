class Catalog:
    def __init__(self, original_filename, filename, url, catalog_type, skip_rows, columns, degree_columns):
        self.original_filename = original_filename
        self.filename = filename
        self.url = url
        self.catalog_type = catalog_type
        self.skip_rows = skip_rows
        self.columns = columns
        self.degree_columns = degree_columns

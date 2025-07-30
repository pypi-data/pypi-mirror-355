# phantom_file_forge
generate dummy data for various MIME types for testing purposes

## Usage

The `generate_dummy_files.py` script allows you to generate dummy files for various MIME types.

### Arguments

- list of MIME types to generate files for.  
    Example: `text/plain image/png`
- `--output-dir` or `-o`: Directory where the generated files will be saved.  
    Example: `--output-dir ./dummy_files`
- `--no-files`: Number of files to generate for each MIME type.  
    Example: `--no-files 5`
- `--min-gb`: Minimum Size (in giga bytes) of each generated file.  
    Example: `--min-gb 0.006`
- `--max-gb`: Maximum Size (in giga bytes) of each generated file.  
    Example: `--max-gb 0.008`

### Example

```bash
phantom_file_forge image/png image/jpeg application/pdf application/vnd.openxmlformats-officedocument.spreadsheetml.sheet application/vnd.openxmlformats-officedocument.presentationml.presentation application/vnd.openxmlformats-officedocument.wordprocessingml.document --no-files 80 -o ./generated_data_set
```

This command generates 80 dummy files for each specified MIME type, each with file size ranging between 6MB and 8MB and saves them in the `./generated_data_set` directory.

Refer to [MDN Common MIME types](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/MIME_types/Common_types) and update the `CUSTOM_MIME_HANDLERS` list in the script for new MIME types as needed.

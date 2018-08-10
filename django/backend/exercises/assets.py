"""Asset file handling."""
import os


def list_assets(path, types):
    all_files = os.listdir(path)
    assets = [{'filename': asset} for asset in all_files if asset.lower().endswith(types)]
    return assets


def has_asset(path, asset):
    file_path = os.path.join(path, asset)
    return os.path.isfile(file_path)


def add_asset(path, asset_file, types):
    """Create asset from uploaded file.

    Args:
        path (str): Path where asset is to be saved.
        asset_file (UploadedFile): Django uploaded file object.
        types (list(str)): List of approved file endings.

    Returns:
        dict: ::

            error (str): Error message
            success (str): Success message

    """
    file_path = os.path.join(path, asset_file.name)
    if not asset_file.name.lower().endswith(types):
        return {'error': 'File type not allowed, valid filetypes are: ' + ', '.join(types)}
    if os.path.isfile(file_path):
        return {'error': 'File already exists.'}
    try:
        with open(file_path, 'wb') as asset:
            for chunk in asset_file.chunks():
                asset.write(chunk)
    except IOError:
        return {'error': "Couldn't write to asset file " + file_path}
    return {'success': 'Wrote file'}


def delete_asset(path, asset_filename):
    file_path = os.path.join(path, asset_filename)
    if not os.path.isfile(file_path):
        return {'error': 'No such file!'}
    try:
        os.remove(file_path)
    except IOError:
        return {'error': "Couldn't delete asset file " + file_path}
    if os.path.isfile(file_path):
        return {'error': "Couldn't delete asset file " + file_path}

    return {'success': 'Deleted file'}

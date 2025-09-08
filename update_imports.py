import os
import re

def update_file_imports(filepath):
    '''Update imports in a Python file to use absolute imports'''
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace relative imports with absolute imports
        # Update utils imports
        content = re.sub(r'from utils\.', 'from emailflow.utils.', content)
        content = re.sub(r'import utils\.', 'import emailflow.utils.', content)
        
        # Update services imports
        content = re.sub(r'from services\.', 'from emailflow.services.', content)
        content = re.sub(r'import services\.', 'import emailflow.services.', content)
        
        # Update routes imports (if any)
        content = re.sub(r'from routes\.', 'from emailflow.routes.', content)
        content = re.sub(r'import routes\.', 'import emailflow.routes.', content)
        
        # Update models imports
        content = re.sub(r'from models ', 'from emailflow.models ', content)
        content = re.sub(r'import models', 'import emailflow.models', content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f'Updated imports in {filepath}')
    except Exception as e:
        print(f'Error updating {filepath}: {e}')

def update_directory_imports(directory):
    '''Recursively update imports in all Python files in a directory'''
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                update_file_imports(filepath)

if __name__ == '__main__':
    # Update imports in routes, services, and utils directories
    directories = ['routes', 'services', 'utils']
    for directory in directories:
        if os.path.exists(directory):
            update_directory_imports(directory)
            print(f'Finished updating imports in {directory}/')
    
    print('Import update complete!')
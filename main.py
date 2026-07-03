import os
import sys
from src.getradon import generate
from src.lib.pycerfl.pycerfl import * 



def get_folder_name(type_option,option):

        clean_input = option.strip().rstrip('/')
        
        if type_option == 'repo-url':
            # Caso URL: https://github.com/user/mi-repo.git -> "mi-repo"
            print(target_folder + 'processed/' +  clean_input.split('/')[-1].replace('.git', ''))
            return target_folder + 'processed/' +  clean_input.split('/')[-1].replace('.git', '')
        
        elif type_option == 'user':
            # Caso Usuario: "nombre-de-usuario" -> "nombre-de-usuario"
            return target_folder + 'processed/' + clean_input.split('/')[-1]
            
        elif type_option == 'directory':
            # Caso Directorio: "/home/user/proyecto" -> "proyecto"
            return target_folder + 'processed/source_directory/'
            
            

# def create_analysis_folder(self):
#         pwd = os.getcwd()
#         folder_path = f"/{self.identifier}"
#         os.makedirs(folder_path, exist_ok=True)
#         return folder_path


def choose_option(type_option,option,target_folder):
    """ Choose option. """
    source_path = None
    target_path = get_folder_name(type_option,option)
    os.makedirs(target_path, exist_ok=True)
    if type_option == 'directory':
        source_path = option
        dir = option.split('/')[-1]        
        print(dir)
        read_Directory(source_path, dir,target_path)
    elif type_option == 'repo-url':
        source_path = request_url(option,target_path)
    elif type_option == 'user':
        source_path = run_user(option,target_path)
    else:
        sys.exit('Incorrect Option')
    return target_path, source_path




if __name__ == "__main__":
    
    try:
        type_option = sys.argv[1]
        option = sys.argv[2]
    except:
        sys.exit("Usage: python3 file.py type-option('directory', " +
                 "'repo-url', 'user') option(directory, url, user)")
    
    target_folder = os.path.dirname(os.path.abspath(__file__)) + "/data/"
  
    processed_path, source_path = choose_option(type_option, option, target_folder)
    
    if source_path is None:
        sys.exit(f"Repo or user under 50% python code : Exiting ")
    summary_Levels(processed_path)
    generate_radon(source_path, processed_path)



    
    



import os
import sys
from src.lib.pycerfl.pycerfl import * 



def get_folder_name(type_option,option):

        clean_input = option.strip().rstrip('/')
        
        if type_option == 'repo-url':
            # Caso URL: https://github.com/user/mi-repo.git -> "mi-repo"
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
    source_path = target_folder + 'raw/'
    target_path = get_folder_name(type_option,option) 
    os.makedirs(target_path, exist_ok=True)
    if type_option == 'directory':
        dir = option.split('/')[-1]        
        print(dir)
        read_Directory(option, dir,target_path)
    elif type_option == 'repo-url':
        request_url(option,)
    elif type_option == 'user':
        run_user(option,target_path)
    else:
        sys.exit('Incorrect Option')



target_path
if __name__ == "__main__":
    
    try:
        type_option = sys.argv[1]
        option = sys.argv[2]
    except:
        sys.exit("Usage: python3 file.py type-option('directory', " +
                 "'repo-url', 'user') option(directory, url, user)")
    
    target_folder = os.path.dirname(os.path.abspath(__file__)) + "/data/"
  
     
    choose_option(type_option, option,target_folder)




    
    



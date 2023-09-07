
from datetime import datetime
class Note:
    def __init__(self,note_id,title,created_by_user_id, tags, content,create_date):
        self.note_id = note_id
        self.title = title 
        self.tags = tags 
        self.content = content
        self.created_by_user_id = created_by_user_id
        self.create_date = create_date
        self.modified_date = datetime.now()
    
    def update_note(self,new_content):
        self.content = new_content
        self.modified_date = datetime.datetime.now()        
        
     
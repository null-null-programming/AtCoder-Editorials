from flask_sqlalchemy import SQLAlchemy,request
from flask_login import  current_user
from config import app, db
from app import Like,Editorial,User

id=request.form['id']
flag=db.session.query(Like).filter(edit_id=id,user_id=current_user.id).first()
edit=db.session.query(Editorial).filter(Editorial.id==id).first()
user=db.session.query(User).filter(User.id==current_user.id).first()

 #いいねされていた場合
newLike=Like(user_id=current_user.id,edit_id=id)
if flag==True:
    edit.like-=1
    user.like_sum-=1
    db.session.delete(newLike)
else:
    edit.like+=1
    user.like_sum+=1
    db.session.add(newLike)

db.session.commit()
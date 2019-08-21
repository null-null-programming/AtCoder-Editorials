from flask import Flask, render_template, request,url_for, redirect,session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_migrate import Migrate
from flask_login import UserMixin, LoginManager, login_user, logout_user, current_user
from datetime import datetime
from rauth import OAuth1Service
from config import app, db, service, login_manager


class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True)
    description = db.Column(db.String(1024), index=True)
    user_image_url = db.Column(db.String(1024), index=True)
    date_published = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    twitter_id = db.Column(db.String(64), nullable=False, unique=True)
    like_sum=db.Column(db.Integer)


class Editorial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64))
    contestname = db.Column(db.String(64))
    title = db.Column(db.String(64))
    url = db.Column(db.String(120))
    description = db.Column(db.String(2048))
    like = db.Column(db.Integer)
    user_image_url = db.Column(db.String(1024), index=True)
    user_id=db.Column(db.Integer)

class Like(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer)
    edit_id=db.Column(db.Integer)

def _normalize_contestname(contestname):
    if isinstance(contestname, str):
        contestname = contestname.strip()
    return contestname


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search', methods=['GET'])
def contest_search():
    return render_template('search.html')


@app.route('/search/contest/<int:page>', methods=['GET','POST'])
def contest_get(page=1):
    contestname = _normalize_contestname(request.form.get('contestname'))
    
    if contestname==None:
        contestname=request.args.get('contestname','')

    per_page = 10
    editorials = db.session.query(Editorial).filter_by(contestname=contestname).order_by(desc(Editorial.like)).paginate(page, per_page, error_out=False)
    print(type(editorials))

    if current_user.is_authenticated==True:
        flag={}
        for edit in editorials.items:
            like=db.session.query(Like).filter(Like.edit_id==edit.id,Like.user_id==current_user.id).first()
            print(like)
            if like:
                flag[edit.id]=True
            else:
                flag[edit.id]=False

        return render_template('contest.html', contestname=contestname, editorials=editorials,flag=flag)
    else:
        return render_template('contest.html',contestname=contestname,editorials=editorials)


@app.route('/submited', methods=['POST'])
def submit():
    params = {
        'title': request.form.get('title'),
        'description': request.form.get('description'),
        'contestname': _normalize_contestname(request.form.get('contestname')),
        'url': request.form.get('url'),
        'like':int(0),
        'user_image_url': current_user.user_image_url,
        'username': current_user.username,
        'user_id':current_user.id
    }   

    params['description']=params['description'].replace('\r\n','<br>')

    if ((params['description'] is not None and params['description'] is not '') or (params['url'] is not None and params['url'] is not ''))\
          and params['title'] is not None and params['title'] is not '':
        newEditorial = Editorial(**params)
        db.session.add(newEditorial)
        db.session.commit()
        return render_template('submited.html')
    else:
        if params['title'] is None:
            return render_template('error.html', message='Error:タイトルを入力して下さい。')
        else:
            return render_template('error.html', message='Error:URLまたは解説文を入力して下さい。')


@app.route('/user/<int:id>/<int:page>',methods=['GET'])
def user(id,page=1):
    per_page=10

    user=User.query.filter_by(id=id).first()
    edit=Editorial.query.filter_by(user_id=id).paginate(page, per_page, error_out=False)

    edit_num=Editorial.query.filter_by(user_id=id).all()
    num=len(edit_num)

    like_set=set([])
    users=db.session.query(User).all()
    for  i in users:
        like_set.add(i.like_sum)
    
    like_set=list(like_set)
    like_set=sorted(like_set,reverse=True)
    
    rank=1
    for i in range(0,len(like_set)):
        if like_set[i]==user.like_sum:
            rank=i+1
            break
    
    return render_template('user.html',user=user,edit=edit,num=num,rank=rank)

@app.route('/ranking/<int:page>')
def ranking(page=1):
    per_page = 100
    users=db.session.query(User).order_by(desc(User.like_sum)).paginate(page, per_page, error_out=False)

    rank=dict({})
    like_set=set([])
    user=db.session.query(User).all()
    for  i in user:
        like_set.add(i.like_sum)
    
    like_set=list(like_set)
    like_set=sorted(like_set,reverse=True)
    
    for i in range(0,len(like_set)):
        rank[like_set[i]]=i+1

    return render_template('ranking.html',users=users,page=page,per_page=per_page,rank=rank)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/oauth/twitter')
def oauth_authorize():
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    else:
        request_token = service.get_request_token(params={
            'oauth_callback': url_for('oauth_callback', provider='twitter', _external=True)
        })
        session['request_token'] = request_token
        return redirect(service.get_authorize_url(request_token[0]))


@app.route('/oauth/twitter/callback')
def oauth_callback():
    request_token = session.pop('request_token')
    oauth_session = service.get_auth_session(
        request_token[0],
        request_token[1],
        data={
            'oauth_verifier': request.args['oauth_verifier']
        }
    )

    profile = oauth_session.get('account/verify_credentials.json').json()

    twitter_id = str(profile.get('id'))
    username = str(profile.get('name'))
    description = str(profile.get('description'))
    profile_image_url = str(profile.get('profile_image_url'))
    user = db.session.query(User).filter(User.twitter_id == twitter_id).first()

    if user:
        user.twitter_id = twitter_id
        user.username = username
    else:
        user = User(
            twitter_id=twitter_id,
            username=username,
            description=description,
            user_image_url=profile_image_url,
            like_sum=int(0)
        )
        db.session.add(user)

    db.session.commit()
    login_user(user, True)
    return redirect(url_for('index'))

@app.route('/like',methods=['POST'])
def like():
    id=request.form['id']
    flag=db.session.query(Like).filter(Like.edit_id==id ).filter(Like.user_id==current_user.id).first()
    edit=db.session.query(Editorial).filter(Editorial.id==id).first()
    user=db.session.query(User).filter(User.id==edit.user_id).first()

    #いいねされていた場合
    newLike=Like(user_id=current_user.id,edit_id=id)
    if flag!=None:
        edit.like-=1
        user.like_sum-=1
        db.session.delete(flag)
    else:
        edit.like+=1
        user.like_sum+=1
        db.session.add(newLike)

    db.session.commit()

    return 'hoge'

@app.route('/delete',methods=['POST'])
def delete():
    edit=db.session.query(Editorial).filter(Editorial.id==request.form['id']).first()

    user=db.session.query(User).filter(User.id==edit.user_id).first()
    user.like_sum-=edit.like

    like=db.session.query(Like).filter(Like.edit_id==edit.id).all()
    for i in like:
        db.session.delete(i)

    db.session.delete(edit)
    db.session.commit()

    return 'hoge'

@app.errorhandler(401)
def authentication_failed(error):
    return render_template('401.html'),401

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'),404

@app.errorhandler(500)
def page_not_found(error):
    return render_template('500.html'),500

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.cli.command('initdb')
def initdb_command():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)

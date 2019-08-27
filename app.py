from flask import Flask, render_template, request,url_for, redirect,session,jsonify,abort, make_response, current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_migrate import Migrate
from flask_login import UserMixin, LoginManager, login_user, logout_user, current_user
from datetime import datetime
from rauth import OAuth1Service
import requests
import json
from config import app, db, service, login_manager,csrf

#ユーザー情報
class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True)
    description = db.Column(db.String(1024), index=True)
    user_image_url = db.Column(db.String(1024), index=True)
    date_published = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    twitter_id = db.Column(db.String(64), nullable=False, unique=True)
    like_sum=db.Column(db.Integer)

#解法情報
class Editorial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64))
    contestname = db.Column(db.String(64))
    title = db.Column(db.String(64))
    url = db.Column(db.String(1024))
    description = db.Column(db.String(3000))
    like = db.Column(db.Integer)
    user_image_url = db.Column(db.String(1024), index=True)
    user_id=db.Column(db.Integer)

#いいね情報
class Like(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer)
    edit_id=db.Column(db.Integer)

#コンテスト名に含まれる空白などを取り除く
def _normalize_contestname(contestname):
    if isinstance(contestname, str):
        contestname = contestname.strip()
    return contestname


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def contest_search():
    #JSON取得　
    get_problem=requests.get('https://kenkoooo.com/atcoder/resources/problems.json')
    get_contest=requests.get('https://kenkoooo.com/atcoder/resources/contests.json')
    #list型に変換
    get_problem=get_problem.json()
    get_contest=get_contest.json()

    #コンテストを新しい順に並び替える
    contest_list=sorted(get_contest,key=lambda x: x['start_epoch_second'],reverse=True)
    #最新のコンテスト名
    contestname=contest_list[0]['id']

    #新着問題を取得する
    problem_list=[]
    for problem in get_problem:
        if problem['contest_id']==contestname:
            problem_list.append((problem['title'],problem['id']))

    return render_template('search.html',problems=problem_list)


@app.route('/search/<problem_id>/<int:page>', methods=['GET','POST'])
def contest_get(problem_id,page=1):
    contestname = _normalize_contestname(request.args.get('contestname'))
    
    get_problem=requests.get('https://kenkoooo.com/atcoder/resources/problems.json')
    get_problem=get_problem.json()

    contest_id=''
    for problem in get_problem:
        if problem_id==problem['id']:
            contest_id=problem['contest_id']
            break

    #ページネーション
    per_page = 10
    editorials = db.session.query(Editorial).filter_by(contestname=contestname).order_by(desc(Editorial.like)).paginate(page, per_page, error_out=False)

    #ログインしている場合は、既にいいねしている「いいね欄」を塗りつぶす
    if current_user.is_authenticated==True:
        flag={}
        for edit in editorials.items:
            like=db.session.query(Like).filter(Like.edit_id==edit.id,Like.user_id==current_user.id).first()
            if like:
                flag[edit.id]=True
            else:
                flag[edit.id]=False

        return render_template('contest.html', contestname=contestname, editorials=editorials,flag=flag,problem_id=problem_id,contest_id=contest_id)
    else:
        return render_template('contest.html',contestname=contestname,editorials=editorials,problem_id=problem_id,contest_id=contest_id)


@app.route('/submited', methods=['POST','GET'])
def submit():
    #DBに挿入する解法情報
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
    
    if params['description']!=None:
            params['description']=params['description'].replace('\r\n','<br>')


    #必要量記入されているかチェック
    if (params['description'] is not None and params['description'] is not '') or ((params['url'] is not None and params['url'] is not '')\
          and (params['title'] is not None and params['title'] is not '')):
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
    user=User.query.filter_by(id=id).first()

    #ページネーション
    per_page=10
    edit=Editorial.query.filter_by(user_id=id).paginate(page, per_page, error_out=False)

    #投稿数
    editorials=Editorial.query.filter_by(user_id=id).all()
    num=len(editorials)

    flag={}
    #ログインしている場合は、既にいいねしている「いいね欄」を塗りつぶす
    if current_user.is_authenticated==True:
        for edit_ in editorials:
            like=db.session.query(Like).filter(Like.edit_id==edit_.id,Like.user_id==current_user.id).first()
            if like:
                flag[edit_.id]=True
            else:
                flag[edit_.id]=False

    #順位計算（繰り上がり処理付き）
    rank_dict=dict({})
    user_list=db.session.query(User).order_by(desc(User.like_sum)).all()

    for  i in user_list:
        rank_dict[i.like_sum]=-1
        
    for i in range(0,len(user_list)):
        if rank_dict[user_list[i].like_sum]!=-1:
            continue
        else:
            rank_dict[user_list[i].like_sum]=i+1
    rank=rank_dict[user.like_sum]
    
    #登録日(何時何分何秒は除いている)
    date_published=str(user.date_published)
    date_published=date_published.split(' ')[0]

    return render_template('user.html',user=user,edit=edit,num=num,rank=rank,flag=flag,date_published=date_published)

@app.route('/ranking/<int:page>')
def ranking(page=1):
    #ページネーション
    per_page = 100
    users=db.session.query(User).order_by(desc(User.like_sum)).paginate(page, per_page, error_out=False)

    #順位計算（繰り上がり処理付き）
    rank=dict({})
    user=db.session.query(User).order_by(desc(User.like_sum)).all()
    for  i in user:
        rank[i.like_sum]=-1
    
    for i in range(0,len(user)):
        if rank[user[i].like_sum]!=-1:
            continue
        else:
            rank[user[i].like_sum]=i+1

    return render_template('ranking.html',users=users,page=page,per_page=per_page,rank=rank)

#Twitterログアウト
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

#Twitterログイン処理
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

#いいね処理
@app.route('/like',methods=['GET'])
def like():
    id=request.args.get('id')

    #いいねを既にされているかどうか
    flag=db.session.query(Like).filter(Like.edit_id==id).filter(Like.user_id==current_user.id).first()
    #解法情報
    edit=db.session.query(Editorial).filter(Editorial.id==id).first()
    #ユーザー情報
    user=db.session.query(User).filter(User.id==edit.user_id).first()

    #既にいいねされていた場合
    newLike=Like(user_id=current_user.id,edit_id=id)
    if flag!=None:
        #解法情報のいいね数と投稿者の総いいね数を減らす
        edit.like-=1
        user.like_sum-=1
        db.session.delete(flag)

    #まだいいねされていなかった場合
    else:
        #解法情報のいいね数と投稿者の総いいね数を増やす
        edit.like+=1
        user.like_sum+=1
        db.session.add(newLike)

    db.session.commit()

    return 'hoge'

#解法消去処理
@app.route('/delete',methods=['GET'])
def delete():
    edit=db.session.query(Editorial).filter(Editorial.id==request.args.get('id')).first()

    #投稿者の総いいね数から、消去する解法のいいね数を減らす
    user=db.session.query(User).filter(User.id==edit.user_id).first()
    user.like_sum-=edit.like

    #いいねテーブルから消去する記事の情報を全て消す
    like=db.session.query(Like).filter(Like.edit_id==edit.id).all()
    for i in like:
        db.session.delete(i)

    db.session.delete(edit)
    db.session.commit()

    return 'hoge'

@app.route('/getName',methods=['GET'])
def getName():
    res=requests.get('https://kenkoooo.com/atcoder/resources/problems.json')
    return jsonify(res.json())


#エラー処理
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
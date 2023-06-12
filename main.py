import datetime
import io
from flask import jsonify, render_template, redirect, request, make_response
from flask_login import login_required, login_user, logout_user, current_user
from flask_socketio import send, emit, join_room, leave_room
from PIL import Image

from config import app, login_manager, db, socketio, blueprint

from static.modules.forms.signup import RegisterForm
from static.modules.forms.auth import LoginForm
from static.modules.forms.edituser import EditUserForm
from static.modules.forms.changeuserpass import ChangeUserPass
from static.modules.forms.newpublication import NewPublForm
from static.modules.forms.editpubl import EditPublForm

from static.modules.users import User
from static.modules.publications import Publication
from static.modules.chatmsgs import ChatMessages
from static.modules.chats import Chats


# for flask login manager
# getting user
@login_manager.user_loader
def load_user(user_id):
    """"Getting user (for flask login manager)"""

    return db.session.get(User, user_id)


# logout
@app.route('/logout')
@login_required
def logout():
    """Logout

    Returns:
        jinja template: html page
    """
    logout_user()
    return redirect("/")


# main page
@app.route('/')
def main_page():
    """"Main page. Contains recent publications"""

    # if we able to show private publications of current user
    if current_user.is_authenticated:
        # get all not private publications of other users and
        # all private publications of current user and reverse array
        # because we need to sort publications by created date
        publications = db.session.query(Publication).filter(
            (Publication.user_id == current_user.id) | (Publication.is_private != 1)).all()[::-1]

    else:
        # get all not private publications and reverse array
        # because we need to sort publications by created date
        publications = db.session.query(Publication).filter(
            Publication.is_private != 1).all()[::-1]

    # getting likes
    likes = request.cookies.get("likes", [])

    # if likes are an empty string, then we make an empty list from it
    # otherwise there will be a TypeError error
    if not likes:
        likes = []

    # forming an array which contains
    # id of publications that the current user has liked
    else:
        likes = [int(item) for item in likes.split(' ')]

    return render_template("main.html",
                           cur_url=request.base_url.split('/')[-1],
                           data=publications,
                           likes=likes)


"""==========USERS=============="""


@app.route('/userava/<int:id>')
@login_required
def userava(id):
    """Getting user's avatar as image

    Args:
        id (int): user's id

    Returns:
        Response: user's image in bytes
    """

    # call method to get avatar in bytes
    img = current_user.getAvatar(app, id)

    # if error
    if not img:
        return ""

    # we need to make response to be able to return it
    avatar = make_response(img)
    avatar.headers['Content-Type'] = 'image/png'
    return avatar


@app.route('/change_avatar/<int:id>', methods=["GET", "POST"])
@login_required
def new_avatar(id):
    """Changing the user's avatar with the transmitted id

    Args:
        id (int): user's id
    """

    # function that cuts out a square fragment from the middle of the image
    def crop_center(pil_img):
        # getting image ize
        width, height = pil_img.size

        # new size
        new_width, new_height = 0, 0

        # if height is greater than width
        # then we need to cut out by height
        if height > width:
            new_height = width
            new_width = width

            return pil_img.crop((0, height // 2 - (new_height // 2), new_width,  height // 2 + (new_height // 2)))

        else:
            new_width = height
            new_height = height

            return pil_img.crop((width // 2 - (new_width // 2), 0, width // 2 + (new_width // 2), new_height))

    # if user clicked Submit button
    if request.method == "POST":
        # getting this user
        user = db.session.query(User).filter(User.id == id).first()

        # getting uploaded image
        file = request.files['newAvatar']
        # checking extension of uploaded image
        ext = file.filename.rsplit('.', 1)[1]
        if ext == "png" or ext == "PNG" or ext == "jpg" or ext == "JPG":
            # open image in PIL
            im = Image.open(io.BytesIO(file.read()))
            # crop image
            im = crop_center(im)
            # convert ready image to bytes
            # because we will upload it to db
            buf = io.BytesIO()
            im.save(buf, format='JPEG')

            # updating avatar
            user.updateUserAvatar(buf.getvalue(), user.id)
            # success, redirect to profile page
            return redirect(f'/profile/{current_user.id}')

    # if user just opened the page without sending
    return render_template("editavatar.html", cur_url=request.base_url.split('/')[-2])


@app.route('/profile/<int:id>', methods=["GET", "POST"])
@login_required
def profile(id):
    """User's profile page

    Args:
        id (int): user's id
    """

    # !!!current user = user with id equal to id argument!!!

    # getting name, surname and bio of current user
    personal_data = db.session.query(
        User.name, User.surname, User.about).filter(User.id == id).one()

    # if a user wants to view their profile
    if id == current_user.id:
        # we can show him his publications
        publications = db.session.query(Publication).filter(
            Publication.user_id == id)
    else:
        # we can show only not private publications
        publications = db.session.query(Publication).filter(Publication.is_private != 1,
                                                            Publication.user_id == id)

    # getting likes
    likes = request.cookies.get("likes", [])

    # if likes are an empty string, then we make an empty list from it
    # otherwise there will be a TypeError error
    if not likes:
        likes = []

    # forming an array which contains
    # id of publications that the current user has liked
    else:
        likes = [int(item) for item in likes.split(' ')]

    # if a user is viewing a profile that is not his own
    # he can create a chat with the profile being viewed
    # or go to it
    create_chat = db.session.query(Chats).filter((Chats.allowed_users.like(
        f'{current_user.id} {id}')) | (Chats.allowed_users.like(f'{id} {current_user.id}'))).first()

    return render_template("profile.html",
                           cur_url=request.base_url.split('/')[-2],
                           id=id,
                           publications=publications[::-1],
                           name=personal_data[0],
                           surname=personal_data[1],
                           about=personal_data[2],
                           likes=likes,
                           create_chat=create_chat)


@app.route('/profile/make_like/<int:publ_id>')
@login_required
def make_like(publ_id):
    """Put like or remove like to publication with publ_id id

    Args:
        publ_id (int): publication's id

    Returns:
        Response
    """

    # getting an array which contains publications id
    likes = request.cookies.get("likes", 0)
    # this is the address where the request came from
    referrer = request.referrer.split('/')
    referrer = '/'.join(referrer[3:])

    # if current user already put likes
    if likes:
        # forming an array of publications id
        likes = [item for item in likes.split(' ')]

        # if current user already liked current publication
        # it means that we need to remove his like
        if str(publ_id) in likes:
            # remove publication id from data array
            likes.remove(str(publ_id))
            # subtract 1 from the number of likes of current publication
            db.session.query(Publication).filter(Publication.id == publ_id).update(
                {'likes_amount': Publication.likes_amount - 1})
            # commit changes
            db.session.commit()
            # make response of redirecting back
            res = make_response(redirect(f'/{referrer}'))
            # changing cookies
            res.set_cookie("likes", ' '.join(likes),
                           max_age=60 * 60 * 24 * 365 * 2)

        else:
            # else we need to like current publication
            # add publication id to data array
            likes.append(str(publ_id))
            # adding 1 to the number of likes of current publication
            db.session.query(Publication).filter(Publication.id == publ_id).update(
                {'likes_amount': Publication.likes_amount + 1})
            # commit changes
            db.session.commit()
            # make response of redirecting back
            res = make_response(redirect(f'/{referrer}'))
            # changing cookies
            res.set_cookie("likes", ' '.join(likes),
                           max_age=60 * 60 * 24 * 365 * 2)

    else:
        # make response of redirecting back
        res = make_response(redirect(f'/{referrer}'))
        # adding 1 to the number of likes of current publication
        db.session.query(Publication).filter(Publication.id == publ_id).update(
            {'likes_amount': Publication.likes_amount + 1})
        # commit changes
        db.session.commit()
        # create cookies
        res.set_cookie("likes", f'{publ_id}',
                       max_age=60 * 60 * 24 * 365 * 2)

    return res


@app.route('/edit_profile/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_profile(id):
    """Edit user data

    Args:
        id (int): user id
    """

    # load form
    form_useredit = EditUserForm()

    # POST
    if form_useredit.validate_on_submit():
        # getting current user
        user = db.session.query(User).filter(User.id == id).first()

        # if user with such an email already exists
        if db.session.query(User).filter(User.email == form_useredit.email.data).first() and \
                form_useredit.email.data != user.email:
            return render_template("edituser.html", cur_url=request.base_url.split('/')[-2],
                                   form_useredit=form_useredit, message="Пользователь с таким email-ом уже есть!")

        # if user exists
        if user:
            # update data
            user.name = form_useredit.name.data
            user.surname = form_useredit.surname.data
            user.email = form_useredit.email.data
            user.about = form_useredit.about.data

        # commit changes
        db.session.commit()
        # redirect to profile page
        return redirect(f'/profile/{id}')

    return render_template("edituser.html",
                           cur_url=request.base_url.split('/')[-2],
                           form_useredit=form_useredit)


@app.route('/change_pass/<int:id>', methods=['GET', 'POST'])
@login_required
def ch_pass(id):
    """Change password

    Args:
        id (int): user id
    """

    # load form
    form_chpass = ChangeUserPass()

    # POST
    if form_chpass.validate_on_submit():
        user = db.session.query(User).filter(User.id == id).first()

        # if current password is incorrect
        if not user.check_password(form_chpass.old_password.data):
            return render_template("chuserpass.html", cur_url=request.base_url.split('/')[-2],
                                   form_chpass=form_chpass, message="Неправильный текущий пароль!")

        # if the entered passwords do not match
        if form_chpass.new_password.data != form_chpass.new_password_repeat.data:
            return render_template("chuserpass.html", cur_url=request.base_url.split('/')[-2],
                                   form_chpass=form_chpass, message="Пароли не совпадают!")

        if user:
            # set new password
            user.set_password(form_chpass.new_password.data)
            # commit changes
            db.session.commit()
            # redirect to profile page
            return redirect(f'/profile/{id}')

    return render_template("chuserpass.html",
                           cur_url=request.base_url.split('/')[-2],
                           form_chpass=form_chpass)


"""============END PROFILE==================="""


@app.route('/members')
def members():
    """Get all members of Zephyr"""

    # getting all users
    data = db.session.query(User).filter(User.id >= 0).all()

    return render_template("members.html", data=data)


@app.route('/friends')
@login_required
def friends():
    """Get all friends of current user

    Returns:
        jinja template: html page
    """

    # get all users the current user is subscribed to
    who_follow_data = current_user.get_who_follow()
    # forming the array which contains User object of every user the current user is subscribed to
    who_follow_data = [db.session.query(User).filter(User.id == item[1]).first()
                       for item in who_follow_data]

    # get all users who are subscribed to current user
    followers_data = current_user.get_followers()
    # forming the array which contains User object of every user who are subscribed to current user
    followers_data = [db.session.query(User).filter(User.id == item[0]).first()
                      for item in followers_data]

    # user entry into both subscriptions and subscribers
    friends_data = list(set(who_follow_data) & set(followers_data))

    # flag of no subscribes
    no_subscribes = not bool(set(who_follow_data) - set(friends_data))
    # flag of no subscribers
    no_subscribers = not bool(set(followers_data) - set(friends_data))

    return render_template("friends.html",
                           cur_url=request.base_url.split('/')[-1],
                           who_follow_data=who_follow_data,
                           followers_data=followers_data,
                           friends_data=friends_data,
                           no_subscribes=no_subscribes,
                           no_subscribers=no_subscribers
                           )


@app.route('/follow/<int:id>')
@login_required
def follow(id):
    """Follow user with id equals to id argument

    Args:
        id (int): following user id
    """

    # this is the address where the request came from
    referrer = request.referrer.split('/')
    referrer = '/'.join(referrer[3:])

    # following user as object
    user = db.session.query(User).filter(User.id == id).first()
    # follow user
    current_user.follow(user)

    # redirect back
    return redirect(f"/{referrer}")


@app.route('/unfollow/<int:id>')
@login_required
def unfollow(id):
    """Unfollow user with id equals to id argument

    Args:
        id (int): unfollowing user id
    """

    # this is the address where the request came from
    referrer = request.referrer.split('/')
    referrer = '/'.join(referrer[3:])

    # desired user as object
    user = db.session.query(User).filter(User.id == id).first()
    # unfollow user
    current_user.unfollow(user)

    # redirect back
    return redirect(f"/{referrer}")


"""============PUBLICATIONS========="""


@app.route('/new_publication/<int:id>', methods=["GET", "POST"])
@login_required
def new_publication(id):
    """Create a new publication with
    the author id equals to id argument

    Args:
        id (int): author id
    """

    # load form
    form_publ = NewPublForm()

    # POST
    if form_publ.validate_on_submit():
        # create new publication as object
        publ = Publication(content=form_publ.content.data,
                           is_private=form_publ.is_private.data,
                           user_id=current_user.id)

        # add to db
        db.session.add(publ)
        # commit changes
        db.session.commit()

        # redirect to profile page
        return redirect(f"/profile/{current_user.id}")

    # GET
    return render_template("newpubl.html", form_publ=form_publ)


@app.route('/edit_publication/<int:id>', methods=["GET", "POST"])
@login_required
def edit_publication(id):
    """Edit existing publication with
    the id equals to id argument

    Args:
        id (int): publication id
    """

    # load form
    form_edit_publ = EditPublForm()
    # this is the address where the request came from
    referrer = request.referrer.split('/')
    referrer = '/'.join(referrer[3:])

    # get requested publication
    publ = db.session.query(Publication).filter(Publication.id == id,
                                                Publication.user_id == current_user.id).first()

    # foolproof. if a person manually enters the address in the browser bar
    # he will not be able to change someone else's publication
    if publ:
        # POST
        if form_edit_publ.validate_on_submit():
            # get data from form
            publ.content = form_edit_publ.content.data

            # commit changes
            db.session.commit()

            # redirect to profile page
            return redirect(f"/profile/{current_user.id}")

        # making the form data equal to the data in the database
        form_edit_publ.content.data = publ.content
        # GET
        return render_template("editpubl.html",
                               form_edit_publ=form_edit_publ,
                               publ=publ)

    else:
        # redirect back
        return redirect(f'/{referrer}')


@app.route('/delete_publication/<int:id>', methods=["GET", "POST"])
@login_required
def delete_publication(id):
    """Delete existing publication with
    the id equals to id argument

    Args:
        id (int): publication id
    """

    # this is the address where the request came from
    referrer = request.referrer.split('/')
    referrer = '/'.join(referrer[3:])

    # get requested publication
    publ = db.session.query(Publication).filter(Publication.id == id,
                                                Publication.user_id == current_user.id).first()

    # foolproof. if a person manually enters the address in the browser bar
    # he will not be able to change someone else's publication
    if publ:
        # delete publication
        db.session.query(Publication).filter(Publication.id == id,
                                             Publication.user_id == current_user.id).delete()
        # commit changes
        db.session.commit()

        # redirect to profile page
        return redirect(f"/profile/{current_user.id}")

    else:
        # redirect back
        return redirect(f'/{referrer}')


"""====================================================="""


@app.route('/signup', methods=['GET', 'POST'])
def register():
    """Register user

    Returns:
        _type_: _description_
    """

    # load form
    form_reg = RegisterForm()

    # POST
    if form_reg.validate_on_submit():
        # if entered passwords do not match
        if form_reg.password.data != form_reg.password_repeat.data:
            return render_template('signup.html', title='Регистрация',
                                   cur_url=request.base_url.split('/')[-1],
                                   form_reg=form_reg,
                                   message="Пароли не совпадают")

        # if such user already exists
        if db.session.query(User).filter(User.email == form_reg.email.data).first():
            return render_template('signup.html', title='Регистрация',
                                   cur_url=request.base_url.split('/')[-1],
                                   form_reg=form_reg,
                                   message="Такой пользователь уже есть")

        # create new user
        user = User(
            name=form_reg.name.data,
            surname=form_reg.surname.data,
            email=form_reg.email.data,
        )

        # set password to new user
        user.set_password(form_reg.password.data)
        # add to db
        db.session.add(user)
        # commit changes
        db.session.commit()

        # redirect to authorization
        return redirect('/auth')

    # GET
    return render_template('signup.html',
                           cur_url=request.base_url.split('/')[-1],
                           title='Регистрация',
                           form_reg=form_reg)


@app.route('/auth', methods=['GET', 'POST'])
def login():
    """Authorization"""

    # load form
    form_auth = LoginForm()

    # POST
    if form_auth.validate_on_submit():
        # look for a user based on the entered data
        user = db.session.query(User).filter(
            User.email == form_auth.email.data).first()

        # if entered data is correct
        if user and user.check_password(form_auth.password.data):
            # login user
            login_user(user, remember=form_auth.remember_me.data)
            # redirect to main page
            return redirect("/")

        # else
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               cur_url=request.base_url.split('/')[-1],
                               form_auth=form_auth)

    # GET
    return render_template('login.html',
                           cur_url=request.base_url.split('/')[-1],
                           form_auth=form_auth)


"""=================CHATS========================"""


@app.route('/new_chat/<int:user_id>')
@login_required
def new_chat(user_id):
    """Creates new chat

    Args:
        user_id (int): companion's id
    """

    # if such a chat has not been created yet
    if not db.session.query(Chats).filter(
        (Chats.allowed_users == f'{current_user.id} {user_id}') |
            (Chats.allowed_users == f'{user_id} {current_user.id}')).first():

        # creating new Chats object
        cur_chat = Chats(allowed_users=f'{current_user.id} {user_id}')
        # add to db
        db.session.add(cur_chat)
        # commit to db
        db.session.commit()

        # creating new service message
        message = ChatMessages(
            author_id=-1, msg='Чат создан!', chat_id=cur_chat.id)
        db.session.add(message)
        db.session.commit()

        # redirect to new chat
        return redirect(f'/chat/{cur_chat.id}')

    # else redirect to chats page
    return redirect('/chats')


def check_all_chats():
    """Mark chats with unread messages
        and forming dict of such chats

    Returns:
        dict: key - chat id, value - chat name
    """

    # getting all chats that the user has access to
    chats = db.session.query(Chats).filter(
        Chats.allowed_users.like(f'%{current_user.id}%')).all()

    # future response
    ans = {}

    # processing each chat
    for item in chats:
        # if chat contains unread messages
        # we need to add "Unread" label
        # to is_unread db cell in chats table
        if db.session.query(ChatMessages).filter(ChatMessages.chat_id == item.id,
                                                 ChatMessages.author_id != current_user.id,
                                                 ChatMessages.who_read.notlike(f'%{current_user.id}%')).all():
            item.is_unread = 1

            # forming chat name
            ans[str(item.id)] = "Чат с " + ', '.join([db.session.query(User.name).filter(
                User.id == id, User.id != current_user.id).first()[0]
                for id in item.allowed_users.split(' ')
                if id != str(current_user.id)])

    # commit changes to db
    db.session.commit()

    return ans


"""=========API=========="""


@blueprint.route('/api/check_chats')
def check_chats():
    """"Calling check_all_chats function"""

    return jsonify(check_all_chats())


@blueprint.route('/api/read_all_msgs/<int:chat_id>/<int:user_id>')
def read_all_msgs(chat_id, user_id):
    """Read all messages in chat with chat_id id

    Args:
        chat_id (int): current chat id
        user_id (int): user who read messages

    Returns:
        dict: status
    """

    try:
        # getting all messages in current chat
        messages = db.session.query(ChatMessages).filter(
            ChatMessages.chat_id == chat_id).all()

        for item in messages:
            # if user haven't read the message yet
            if str(user_id) not in item.who_read:
                # add user_id to who_read field
                item.who_read = ' '.join([item.who_read, str(user_id)]).strip()
        # commit changes
        db.session.commit()

    except Exception:
        return jsonify({"message": "error"})

    return jsonify({"message": "success"})


"""=========API-END=========="""


@app.route('/chats')
@login_required
def get_chats():
    """Triggered when user goes to the chat page

    Returns:
        jinja template: html page
    """

    # getting all chats that the user has access to
    chats = db.session.query(Chats).filter(
        Chats.allowed_users.like(f'%{current_user.id}%')).all()

    # reforming the chats array to array which contains
    # Chat object and name of this Chat object relative to the companion's name
    chats = [(item, "Чат с " + ', '.join([db.session.query(User.name).filter(
        User.id == id,
        User.id != current_user.id).first()[0]
        for id in item.allowed_users.split(' ')
        if id != str(current_user.id)])) for item in chats]

    # dict which contains chats with unread messages
    unread = dict(check_all_chats())
    unread = {int(item): unread[item] for item in unread.keys()}

    return render_template("chats.html",
                           chats=chats[::-1],
                           unread=unread,
                           cur_url=request.base_url.split('/')[-1])


@app.route('/chat/<int:id>')
@login_required
def chat(id):
    """Triggered when user clicks on Enter chat button

    Args:
        id (int): current chat id

    Returns:
        jinja template: html page
    """

    # current chat
    cur_chat = db.session.query(Chats).filter(Chats.id == id).first()

    # get companion data
    # companion id
    companion_id = cur_chat.allowed_users.split(' ')
    companion_id = int(companion_id[0]) if int(
        companion_id[0]) != current_user.id else int(companion_id[1])
    # companion as User object
    companion = db.session.query(User).filter(
        User.id == companion_id).first()

    # get all messages in current chat
    data = db.session.query(ChatMessages).filter(
        ChatMessages.chat_id == id).all()

    # remake data array to array which contains
    # sender's name and text of every message in cur chat
    data = [(db.session.query(User.name).filter(
        User.id == item.author_id).first()[0], item.msg) for item in data]

    return render_template('chatwuser.html',
                           cur_url=request.base_url.split('/')[-2],
                           user=current_user,
                           data=data,
                           cur_chat=cur_chat,
                           companion=companion)


@socketio.on('join')
def on_join(data):
    """Function is triggered when the user enters the chat

    Args:
        data (dict): contains current chat name
    """

    # join room
    room = data['chat_name']
    join_room(room)

    # init current chat
    cur_chat = db.session.query(Chats).filter(
        Chats.id == int(request.referrer.split('/')[-1])).first()

    # read all messages in current chat
    read_all_msgs(cur_chat.id, current_user.id)

    # get all messages in current chat
    data = db.session.query(ChatMessages).filter(
        ChatMessages.chat_id == cur_chat.id).all()

    # forming an array
    # cycle through all messages in current chat
    # Args
    # 1 - sender's name
    # 2 - text
    # 3 - sender's id
    # 4 - date and time of dispatch
    data_msg = {i: [db.session.query(User.name).filter(User.id == item.author_id).first()[0],
                    item.msg,
                    item.author_id,
                    (item.date, item.time)]
                for i, item in enumerate(data)}

    # show messages to client
    emit('show_messages', data_msg, broadcast=False)


@socketio.on('leave')
def on_leave(data):
    """Function is triggered when the user leaves the chat

    Args:
        data (dict): contains current chat name
    """

    room = data['chat_name']
    leave_room(room)


@socketio.on('message')
def handle_message(data):
    """Function is triggered when a message is sent by the client

    Args:
        data (dict): contains the text of the message,
            the sender's id and the current chat name
    """

    # if message is not empty
    if len(data['msg']):
        # current chat
        cur_chat = db.session.query(Chats).filter(
            Chats.id == int(request.referrer.split('/')[-1])).first()

        # create new message and add it to session
        message = ChatMessages(
            author_id=data['user_id'], msg=data['msg'], chat_id=cur_chat.id,
            date=datetime.datetime.now().strftime("%d %B %Y"),
            time=datetime.datetime.now().strftime("%H:%M"))
        db.session.add(message)

        # add sender's username to data dict
        data['username'] = db.session.query(User.name).filter(
            User.id == data['user_id']).first()[0]

        # add current date and time to data dict
        data['msg_date'] = datetime.datetime.now().strftime("%d %B %Y")
        data['msg_time'] = datetime.datetime.now().strftime("%H:%M")

        # show message
        send(data, broadcast=True, room=data['chat_name'])

        # commit to database
        db.session.commit()


if __name__ == '__main__':
    # create all tables
    with app.app_context():
        db.create_all()

    # create api
    app.register_blueprint(blueprint)

    # run the app
    socketio.run(app, debug=True)

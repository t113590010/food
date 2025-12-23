
from flask import Flask,render_template,request,redirect, url_for, session, Response
from datetime import datetime
from werkzeug.utils import secure_filename
import db,random, string,os
app = Flask(__name__, template_folder='', static_folder='')
app.secret_key = "A" 
length = 4

#資歷表(新資料表在這引入 之後都用table.名稱 方便管理)
class Table:
    users= 'users'
    food='food'
    food_type='food_type'
    food_rating='food_rating'
table = Table()
#圖片上傳過濾
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True) 

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#sql用法
# data = db.sel("students",1) 
# del
# db.delete("students",{"id":2})
# upd 
# db.upd("students",{"name":"帥哥"},{"id":4})
# sel
# db.sel("students",1) 
# db.sel("students",{"id":5})
# ins 
# db.ins("students",{"name":"大帥哥","score":50})


@app.route('/')
def home():
   
    url = request.args.get('edit')or '1'
        
    upd_food_url = request.args.get('upd')
    upd_food_data = None
    food = db.sel(table.food)
    food_types = db.sel(table.food_type)
    if 'user' not in session :
        if(url == '1'):
            return render_template("index.html",url=url,food_types= food_types,upd_food_data=upd_food_data )
            
        else:
            return  db.alert('未登入','/login')
    
    
    if url == '2' and session['user']['level']!=1:
        users = db.sel(table.users,{'id':session['user']['id']})
        return render_template("index.html",user= session['user'],url=url,users =users)
    
    #訂單管理
    if url == '5':
        if(session['user']['level']==1):
            for f in food:
                user_data = db.sel(table.users, {'id': f['user_id']})
                if user_data:
                    f['user_name'] = user_data[0]['name']
                    f['user_email'] = user_data[0]['email']
        else:
            food = db.sel(table.food,{'user_id':session['user']['id']})
            for f in food:
                print('測試')
                f['user_name'] = session['user']['name']
                f['user_email'] =session['user']['email']
    print(food)



    if upd_food_url:
        upd_food_url = int(upd_food_url)
        for f in food:
            if f['id'] == upd_food_url:
                # --- 加工資料 ---
                if(session['user']['level']==1):
                    user_data = db.sel(table.users, {'id': f['user_id']})
                    f['user_name'] = user_data[0]['name']
                    f['user_email'] = user_data[0]['email']
                else:
                    f['user_name'] =  session['user']['name']
                    f['user_email'] = session['user']['email']

                f['food_types'] = []
                f['food_names'] = []
                f['total_price'] = 0

                # 確保 food_type_id 是 list
                food_type_ids = f['food_type_id']
                if not isinstance(food_type_ids, list):
                    food_type_ids = [food_type_ids]

                for fid in food_type_ids:
                    food_type_data = db.sel(table.food_type, {'id': fid})
                    if food_type_data:
                        ft = food_type_data[0]
                        f['food_types'].append({
                            'name': ft['name'],
                            'unit_price': ft['price']
                        })
                        f['food_names'].append(ft['name'])
                        f['total_price'] += ft['price']

                f['food_names'] = ", ".join(f['food_names'])
                upd_food_data = f
                break


    # print(food)

    food_types = db.sel(table.food_type)
    users = db.sel(table.users)
    # print(session['user'])
    print(upd_food_data)

    # print(users)
    return render_template("index.html", food=food,user= session['user'],url=url, food_types=food_types,users =users,upd_food_data=upd_food_data)


# --- navbar ---
@app.route('/navbar')
def navbar():
    return render_template('navbar.html')


@app.route('/upd_del_done_food', methods=['POST'])
def upd_del_done_food():
    id = request.form.get('upd') or request.form.get('del') or request.form.get('done')or request.form.get('Nodone')
    # print(request.form)
    if 'Nodone' in request.form:
        db.upd(table.food,{'done':0},{'id':id})   
    if 'done' in request.form:
        db.upd(table.food,{'done':1},{'id':id})   
    if 'upd' in request.form:
        counts_raw = {k[6:-1]: int(v[0]) for k, v in request.form.to_dict(flat=False).items() if k.startswith('count[')}

        food_type_ids = [int(fid) for fid in counts_raw.keys()]
        counts = list(counts_raw.values())
        total_price = sum(
            db.sel(table.food_type, {'id': int(fid)})[0]['price'] * qty
            for fid, qty in zip(food_type_ids, counts)
        )

        # 更新資料庫
        update_data = {
            'food_type_id': food_type_ids,
            'food_counts': counts,
            'total': total_price
        }

        db.upd(table.food,update_data,{'id':id})   
        # print(update_data)
        return redirect(url_for('home', upd=id))
        
    if 'del' in request.form:
        db.delete(table.food, {"id": id})
    return redirect(url_for('home', edit='5'))


@app.route('/UpdAndDelFoods', methods=['POST'])
def UpdAndDelFoods():
    id = request.form.get('upd') or request.form.get('del')

    if 'upd' in request.form:
        return redirect(url_for('home', upd=id))
        
    if 'del' in request.form:
        db.delete(table.food, {"id": id})

    return redirect(url_for('home', edit='5'))


@app.route('/tmp_food', methods=['POST'])
def tmp_food():
    if 'user' not in session:
        return db.alert("請先登入", "/login")

    user = session['user']
    form_data = request.form.to_dict(flat=False)

    # 解析 count[ID]，配合 HTML
    counts_dict = {k[6:-1]: v for k, v in form_data.items() if k.startswith('count[')}

    ids = []
    counts = []
    names=[]
    prices= []

    total = 0
    print(form_data,counts_dict)

    for food_id_str, qty_list in counts_dict.items():
        try:
            qty = int(qty_list[0])
        except (ValueError, IndexError):
            continue

        if qty <= 0:
            continue

        food_type_data = db.sel(table.food_type, {'id': int(food_id_str)})
        if not food_type_data:
            print(f"找不到 food_type id={food_id_str}", flush=True)
            continue

        food_type = food_type_data[0]
        ids.append(food_type['id'])
        counts.append(qty)
        total += qty * food_type['price']
        names.append(food_type['name'])
        prices.append(food_type['price'])


    session['tmp_order'] = {
        "food_type_ids": ids,
        "food_type_names":names,
        "counts": counts,
        "prices": prices,
        "total": total,
   
    }

    print("暫存訂單:", session['tmp_order'], flush=True)

    # 跳到下一頁填寫個人資料
    return redirect(url_for('home', edit=4))




@app.route('/add_food', methods=['POST'])
def add_food():
    if 'user' not in session:
        return db.alert("請先登入", "/login")

    user = session['user']
    order = session['tmp_order']
    content = request.form.get('content')
    # print(order)

    db.ins(table.food, {
        'user_id':user['id'],
        'content':content,
        'date':datetime.now(),
        'food_counts':order['counts'],
        'food_type_id':order['food_type_ids'],
        'total':order['total'],
    })
    session.pop('tmp_order', None)
    return redirect(url_for('home', edit='1'))





@app.route('/add_foodtype', methods=['POST'])
def add_foodtype():
    name = request.form.get('name')
    price = request.form.get('price')
    content = request.form.get('content')

   
    if 'img' not in request.files:
        return db.alert("請上傳圖片", "/?edit=3")
    
    file = request.files['img']

    if file.filename == '':
        return db.alert("未選擇圖片", "/?edit=3")

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename) + str(int(time.time())) 
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)  

        target = db.sel("food_type", {'name': name})
        if target:
            return db.alert('已有此類型菜單', '/')

        db.ins("food_type", {
            "name": name,
            "price": int(price),
            "content": content,
            "img": filepath   ,
            "rating_ids": []
        })

        return redirect(url_for('home', edit='3'))

    else:
        return db.alert("檔案格式不支援", "/?edit=3")

@app.route('/UpdAndDelFoodType', methods=['POST'])
def UpdAndDelfoodType():
    id = request.form.get('upd') or request.form.get('del')

    if 'upd' in request.form:
        name = request.form.get('name')
        price = request.form.get('price')
        content = request.form.get('content')
        update_data = {
            "name": name,
            "price": int(price),
            "content": content
        }

        file = request.files.get('img')
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename) + str(int(time.time())) 
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            update_data['img'] = filepath  

        db.upd("food_type", update_data, {"id": id})

    if 'del' in request.form:
        db.delete("food_type", {"id": id})

    return redirect(url_for('home', edit='3'))

@app.route('/all_table')
def all_table():
    tables = db.selTables()
    return render_template('table.html',tables=tables)


@app.route("/captcha.svg")
def captcha_svg():
    text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    session['captcha'] = text  

  
    svg = f'''
    <svg xmlns="http://www.w3.org/2000/svg" width="150" height="50">
      <rect width="150" height="50" fill="white"/>
      <text x="10" y="35" font-size="30" fill="black" font-family="Arial">{text}</text>
    </svg>
    '''
    return Response(svg, mimetype='image/svg+xml')



@app.route('/logout', methods=['POST'])
def logout():
    if 'user' in session:
        session.pop('user', None)

    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if 'user' in session:
        return redirect(url_for('index',edit='1'))

    # tables = db.selTables()
    islogin = True
 
    return render_template("login.html",islogin =islogin)



# @app.route('/booking')
# def booking():
#     if 'user' not in session:
#         return  db.alert('未登入','/login.html')
#     url = request.args.get('edit')or '3'

#     food = db.sel("food",1,'booking_id')
#     food_types = db.sel("food_type", 1)
#     users = db.sel('users')
#     print(session['user'])
#     for all in food:
#         price = db.sel('food_type',{'name':all['food_type']})[0]['price']
#         all['price']= price*(all['check_outdate'] - all['check_indate']).days
#         print(all)
#     return render_template("booking.html", students=food,user= session['user'],url=url, food_types=food_types,users =users
# )

@app.route('/login_check', methods=['POST'])
def login_check():
    acc = request.form.get('acc')
    ps = request.form.get('ps')
    captcha = request.form.get('captcha')
    check_cap= captcha.upper() == session.get('captcha', '').upper()
    checkAcc = db.sel(table.users,{'account':acc,'password':ps})
    if(checkAcc and check_cap):
        user = checkAcc[0]
        session['user'] = user
        return redirect(url_for('home',edit='1'))
    else:
        return db.alert("帳號、密碼或驗證碼錯誤",'login')
 




@app.route('/newAcc', methods=['POST'])
def newAcc():
    acc = request.form.get('acc')
    ps = request.form.get('ps')
    email = request.form.get('email')
    name = request.form.get('name')
    checkAcc = db.sel(table.users,{'account':acc})
    checkEmail = db.sel(table.users,{'email':email})
    
    if(checkAcc or checkEmail):
        return db.alert("已有此帳號或此信箱已被註冊",'/login')
    db.ins(table.users,{'account':acc,'password':ps,'level':0,'email':email,'name':name})
    return db.alert("註冊成功",'/login')

@app.route('/UpdAndDelUsers', methods=['POST'])
def UpdAndDelUsers():
    id = int( request.form.get('upd') or request.form.get('del'))

    if 'upd' in request.form:
        account = request.form.get('account')
        password = request.form.get('password')
        name = request.form.get('name')
        email = request.form.get('email')
        level = int(request.form.get('level'))
        checkAcc = db.sel(table.users,{'account':account})
        checkEmail = db.sel(table.users,{'email':email})
        
        if( (checkAcc and id!= checkAcc[0]['id']) or (checkEmail and id != checkEmail[0]['id'])):
            return db.alert("已有此帳號或此信箱已被註冊",'/?edit=2')
        db.upd(table.users, {
            "password": int(password),
            "account": account,
            "name": name,
            "email": email,
            "level": level,
        }, {"id": id})

    if 'del' in request.form:
        db.delete(table.users, {"id": id})

    return redirect(url_for('home',edit='2'))


@app.route('/DelTable', methods=['POST'])
def DelTable():
    table_name = request.form.get('del')
    if table_name:
        db.drop_table(table_name)
    return redirect(url_for('home'))

if __name__=='__main__':

    app.run(debug = True)






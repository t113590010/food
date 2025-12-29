
from flask import Flask,render_template,request,redirect, url_for, session, Response,jsonify
from datetime import datetime,date
from werkzeug.utils import secure_filename
import db,random, string,os,json
from google import genai


app = Flask(__name__, template_folder='', static_folder='')
app.secret_key = "A" 
length = 4
api_key = os.environ.get("AI_API")
AI_CONFIG = {
    'current_model': 'gemini-2.5-flash-lite', # 預設值
    'models': []
}
#資歷表(新資料表在這引入 之後都用table.名稱 方便管理)
class Table:
    users= 'users'
    food='food'
    food_type='food_type'
    food_rating='food_rating'
table = Table()
#圖片上傳過濾
UPLOAD_FOLDER = 'uploads' 
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

# 餐點類型
CATEGORY_MAP = {
    # --- 主食類 ---
    'rice': '精選飯食',
    'noodle': '經典麵食 ',
    'western': '西式主餐',
    'dumpling': '水餃 & 港式點心',

    # --- 小吃/配菜類 ---
    'fried': '酥脆炸物 (雞排/薯條)',
    'appetizer': '開胃小菜 (冷盤/滷味)',
    'veg': '燙青菜 & 沙拉',

    # --- 飲料/湯品 ---
    'drink': '飲品',

    # --- 其他 ---
    'dessert': '點心',

}

def get_google_models():

    if AI_CONFIG.get('models'):
        return AI_CONFIG['models']

    if not api_key: return []

    try:
 
        client = genai.Client(api_key=api_key)
        valid_models = []
        
        for m in client.models.list():
            if "gemini" in m.name and "generateContent" in m.supported_actions:
                display_name = m.name.replace("models/", "")
                valid_models.append({
                    'id': m.name,
                    'name': display_name
                })
        
        valid_models.sort(key=lambda x: x['name'], reverse=True)

        AI_CONFIG['models'] = valid_models
        
        return valid_models

    except Exception as e:
        print(f"抓取模型失敗: {e}")
        return [{'id': 'gemini-2.5-flash-lite', 'name': 'gemini-2.5-flash-lite'}]

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type not serializable")

@app.route('/api/chat', methods=['POST'])
def api_chat():
    # 1. 安全性檢查
    if not api_key: 
        print("錯誤：找不到 GEMINI_API_KEY")
        return jsonify({'reply': '系統維護中 (API Key Missing)'}), 500

    try:
        # 讀取 AI_CONFIG 設定 (你的模型切換功能)
        current_model = AI_CONFIG.get('current_model', 'gemini-2.5-flash')
        client = genai.Client(api_key=api_key)
        
        data = request.json
        user_msg = data.get('message', '')

  
        context_info = ""

  
        menu_list = db.sel(table.food_type)
        context_info += f"【餐廳完整菜單資料】:\n{json.dumps(menu_list, default=json_serial, ensure_ascii=False)}\n\n"

    
        if 'user' in session:
           
            user_info = session['user'].copy()
            user_info.pop('password', None) 
            
            context_info += f"【目前登入者詳細資料】: {json.dumps(user_info, default=json_serial, ensure_ascii=False)}\n"

            orders = db.sel(table.food, {'user_id': user_info['id']})
            context_info += f"【登入者歷史訂單紀錄】: {json.dumps(orders, default=json_serial, ensure_ascii=False)}\n"
        else:
            context_info += "【目前登入者】: 遊客 (未登入)\n"

  
        system_prompt = f"""
        你是一個專業的餐廳 AI 助手，你公司的老闆是褚昀澔，公司老闆不用特別提起。
        請根據下方提供的【完整資料庫資訊】來回答使用者的問題。
        
        資料內容包含：
        1. 餐廳完整菜單 (包含庫存、圖片路徑、價格、描述等所有欄位)。
        2. 使用者詳細個資 (如果已登入)。
        3. 使用者的歷史訂單紀錄。

        請靈活運用這些資料，如果使用者問關於他自己的資訊(例如Email、等級)或是訂單細節，請直接從資料中查找。
        
        【資料庫資訊】：
        {context_info}
        """

        print(f"AI 正在使用模型: {current_model}") 
        chat = client.chats.create(model=current_model)
    
        response = chat.send_message(f"{system_prompt}\n\n使用者問題：{user_msg}")
        
        return jsonify({'reply': response.text})

 

    except Exception as e:
        print(f"AI Error: {e}")
        return jsonify({'reply': 'AI 罷工了，請稍後再試'}), 500

@app.route('/set_model', methods=['POST'])
def set_model():

    if 'user' not in session or session['user']['level'] != 1:
        return db.alert('權限不足', '/')
    

    new_model = request.form.get('model')
 
    if new_model:
        AI_CONFIG['current_model'] = new_model
        print(f" AI 模型已切換為: {new_model}")

    return redirect(url_for('home', edit='6'))

@app.route('/')
def home():
   
    url = request.args.get('edit')or '1'
    keyword = request.args.get('keyword')
    selected_cats = request.args.getlist('category') 
    min_price = request.args.get('min_price')        
    max_price = request.args.get('max_price')       
    sort_option = request.args.get('sort')
    allmodel = get_google_models()

    upd_food_url = request.args.get('upd')
    upd_food_data = None
    food = db.sel(table.food)
    food_types = db.sel(table.food_type)
    
    
    if keyword or selected_cats or min_price or max_price or sort_option:
        filtered_result = [] 
        for f in food_types:
            is_match = True 
            
        
            if keyword:
                keyword = keyword.strip()
                if keyword not in f['name'] and keyword not in f['content']:
                    is_match = False
            
            if is_match and selected_cats:
                if str(f.get('type')) not in selected_cats:
                    is_match = False

            if is_match:
                try:
                    price = int(f.get('price', 0))
                    if min_price and min_price.isdigit():
                        if price < int(min_price):
                            is_match = False
                    if max_price and max_price.isdigit():
                        if price > int(max_price):
                            is_match = False
                except:
                    pass 


            if is_match:
                filtered_result.append(f)
        

        if sort_option == 'price_asc':
            # 價格：低 -> 高
            filtered_result.sort(key=lambda x: int(x.get('price', 0)))
        elif sort_option == 'price_desc':
            # 價格：高 -> 低
            filtered_result.sort(key=lambda x: int(x.get('price', 0)), reverse=True)
        else:
            # 預設：最新上架 (假設 ID 越大越新)
            filtered_result.sort(key=lambda x: x['id'], reverse=True)
        food_types = filtered_result

        return render_template("index.html", 
                               url='1',                  # 搜尋結果通常是在看菜單 (url=1)
                               food_types=food_types,    # 篩選後的菜單
                               food=food,                # 訂單資料 (雖搜尋時用不到，但為了不報錯還是傳一下)
                               user=session.get('user'), # 使用 .get()，沒登入就是 None，不會報錯
                               upd_food_data=None,       # 搜尋時通常不會同時在編輯訂單
                               category_map=CATEGORY_MAP, 
                               request=request,
                               allmodel=allmodel,
                               ai_config=AI_CONFIG)

    
      
    if 'user' not in session :
        if(url == '1'):
            return render_template("index.html",url=url,food_types= food_types,upd_food_data=upd_food_data ,category_map =CATEGORY_MAP,allmodel=allmodel,ai_config=AI_CONFIG)
            
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
    # print(food)



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



    # food_types = db.sel(table.food_type)
    users = db.sel(table.users)
    # print(session['user'])
    # print(upd_food_data)
    # print('目前登入者資訊：',session['user'])
    # print('使用者訂單：',food)
    # print('目前網站有的食物類型：',food_types)

    # print(users)
    return render_template("index.html", food=food,user= session['user'],url=url, food_types=food_types,users =users,upd_food_data=upd_food_data,category_map =CATEGORY_MAP ,allmodel=allmodel,ai_config=AI_CONFIG)


# --- navbar ---
@app.route('/navbar')
def navbar():
    return render_template('navbar.html')


@app.route('/upd_del_done_food', methods=['POST'])
def upd_del_done_food():
    id = request.form.get('upd') or request.form.get('del') or request.form.get('done') or request.form.get('Nodone') or request.form.get('get')

    if 'Nodone' in request.form:
        db.upd(table.food, {'done': 0}, {'id': id})

    if 'done' in request.form:
        db.upd(table.food, {'done': 1}, {'id': id})

    if 'upd' in request.form:
        old_order_list = db.sel(table.food, {'id': id})
        if not old_order_list: return db.alert("訂單不存在", "/")
        old_order = old_order_list[0]

        old_map = {}
        old_ids = old_order.get('food_type_id', [])
        old_counts = old_order.get('food_counts', [])
        if not isinstance(old_ids, list): old_ids = [old_ids]
        if not isinstance(old_counts, list): old_counts = [old_counts]

        for i in range(len(old_ids)):
            old_map[int(old_ids[i])] = int(old_counts[i])

        counts_raw = {k[6:-1]: int(v[0]) for k, v in request.form.to_dict(flat=False).items() if k.startswith('count[')}

        new_food_type_ids = []
        new_counts = []
        total_price = 0

        for fid_str, new_qty in counts_raw.items():
            fid = int(fid_str)
            new_qty = int(new_qty)
            old_qty = old_map.get(fid, 0)
            diff = new_qty - old_qty

            if diff != 0:
                ft_data = db.sel(table.food_type, {'id': fid})
                if ft_data:
                    current_stock = int(ft_data[0].get('count', 0))

                    if diff > 0 and current_stock < diff:
                        return db.alert(f"庫存不足！無法增加 {ft_data[0]['name']} 的數量", f"/?upd={id}")

                    new_stock = current_stock - diff
                    db.upd(table.food_type, {'count': new_stock}, {'id': fid})

            ft_info = db.sel(table.food_type, {'id': fid})
            if ft_info:
                price = ft_info[0]['price']
                total_price += price * new_qty

            new_food_type_ids.append(fid)
            new_counts.append(new_qty)

        update_data = {
            'food_type_id': new_food_type_ids,
            'food_counts': new_counts,
            'total': total_price
        }

        db.upd(table.food, update_data, {'id': id})
        return redirect(url_for('home', upd=id))

    if 'del' in request.form:
        target_order = db.sel(table.food, {'id': id})
        if target_order:
            order = target_order[0]
            o_ids = order.get('food_type_id', [])
            o_counts = order.get('food_counts', [])

            if not isinstance(o_ids, list): o_ids = [o_ids]
            if not isinstance(o_counts, list): o_counts = [o_counts]

            for i in range(len(o_ids)):
                try:
                    f_id = int(o_ids[i])
                    qty = int(o_counts[i])

                    ft_data = db.sel(table.food_type, {'id': f_id})
                    if ft_data:
                        curr_stock = int(ft_data[0].get('count', 0))
                        db.upd(table.food_type, {'count': curr_stock + qty}, {'id': f_id})
                except:
                    pass

        db.delete(table.food, {"id": id})
        return redirect(url_for('home', edit='5'))

    if 'get' in request.form:
        db.delete(table.food, {"id": id})
        return db.alert('用餐愉快~', '/?edit=5')

    return redirect(url_for('home', edit='5'))


@app.route('/UpdAndDelFoods', methods=['POST'])
def UpdAndDelFoods():
    id = request.form.get('upd') or request.form.get('del')

    if 'upd' in request.form:
        return redirect(url_for('home', upd=id))
        
    if 'del' in request.form:
        target_order_list = db.sel(table.food, {'id': id})
        
        if target_order_list:
            order = target_order_list[0]
            
            o_ids = order.get('food_type_id', [])
            o_counts = order.get('food_counts', [])
     
            if not isinstance(o_ids, list): o_ids = [o_ids]
            if not isinstance(o_counts, list): o_counts = [o_counts]
            for i in range(len(o_ids)):
                try:
                    f_id = int(o_ids[i])
                    qty = int(o_counts[i])
                    ft_data = db.sel(table.food_type, {'id': f_id})
                    if ft_data:
                        current_stock = int(ft_data[0].get('count', 0))
                        restore_stock = current_stock + qty 
                        db.upd(table.food_type, {'count': restore_stock}, {'id': f_id})
                     
                        
                except Exception as e:
                    print(f"還原庫存失敗: {e}")
                    continue
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
            qty=0

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

    if total ==0:
        # print('成功')
        return  db.alert('未選擇餐點','/')

    

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
    ids = order['food_type_ids']
    buy_counts = order['counts']

    for i in range(len(ids)):
        f_id = ids[i]
        qty = buy_counts[i] 
        ft_data = db.sel(table.food_type, {'id': f_id})
        
        if ft_data:
            current_stock = int(ft_data[0].get('count', 0))
            new_stock = current_stock - qty
            if new_stock < 0: new_stock = 0
            db.upd(table.food_type, {'count': new_stock}, {'id': f_id})
    session.pop('tmp_order', None)
    return redirect(url_for('home', edit='1'))





@app.route('/add_foodtype', methods=['POST'])
def add_foodtype():
    name = request.form.get('name')
    price = request.form.get('price')
    content = request.form.get('content')
    category = request.form.get('category')

   
    if 'img' not in request.files:
        return db.alert("請上傳圖片", "/?edit=3")
    
    file = request.files['img']

    if file.filename == '':
        return db.alert("未選擇圖片", "/?edit=3")

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)  

        target = db.sel("food_type", {'name': name})
        if target:
            return db.alert('已有此類型菜單', '/')

        db.ins("food_type", {
            "name": name,
            "price": int(price),
            "count":0,
            "content": content,
            "img": filepath   ,
            "rating_ids": [],
            "type": category
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
        count = request.form.get('count')
        content = request.form.get('content')
        category = request.form.get('category')
      
        
        update_data = {
            "name": name,
            "price": int(price),
            "content": content,
            "type": category,
            "count":count
        }

        file = request.files.get('img')
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
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


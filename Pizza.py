import os
import psycopg2
from datetime import datetime
from flask import Flask, render_template, request, redirect
from dotenv import load_dotenv


app = Flask(__name__)

load_dotenv()

storeID = 0
orderList = []
orderID = 0
customerName = 0
customerAddress = 0
placementTime = 0
pizzaList = []

class Pizza:
    def __init__(self, pizzaID, orderID, size, bellPepper, jalapeno, olive, pepperoni, pineapple, sausage, price):
        self.pizzaID = pizzaID
        self.orderID = orderID
        self.size = size
        self.bellPepper = bellPepper
        self.jalapeno = jalapeno
        self.olive = olive
        self.pepperoni = pepperoni
        self.pineapple = pineapple
        self.sausage = sausage
        self.price = price

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Please define it in a .env file.")

conn = psycopg2.connect(DATABASE_URL)

@app.route('/')
def index():
    return render_template('homepage.html')

@app.route('/managerpage')
def managerpage():
    return render_template('managerpage.html')

@app.route('/managerlogin', methods=['POST'])
def managerlogin():
    global storeID
    storeID = request.form['storeID']
    managerID = request.form['managerID']
    managerPassword = request.form['managerPassword']
    cur = conn.cursor()

    cur.execute("SELECT s_storeID FROM store WHERE s_storeid = %s AND s_managerid = %s AND s_managerpassword = %s;",
                   (storeID, managerID, managerPassword))
    result = cur.fetchone()
    cur.close()
    if result:
        return redirect('/storepage')
    else:
        return render_template('managerpage.html', header="Invalid credentials. Please try again.")
    
@app.route('/storepage')
def inventorypage():
    global storeID
    cur = conn.cursor()
    cur.execute("SELECT si_ingredientID,i_name,si_quantity FROM storeInventory JOIN ingredient ON si_ingredientID = i_ingredientID WHERE si_storeID = %s ORDER BY si_ingredientID;", 
                   (storeID,))
    result = cur.fetchall()
    cur.execute("SELECT o_orderID, o_customerName, o_deliveryAddress, o_orderplacementtime,o_totalprice FROM orders WHERE o_storeID = %s ORDER BY o_orderplacementTime DESC LIMIT 5;",
                (storeID,))
    result2 = cur.fetchall()
    cur.close()
    return render_template('storepage.html', ingredients = result, orders = result2)

@app.route('/quantityUpdate', methods=['POST'])
def quantityUpdate():
    global storeID
    cur = conn.cursor()
    cur.execute("UPDATE storeInventory SET si_quantity = %s WHERE si_storeID = %s AND si_ingredientID = %s;", 
                   (request.form['quantityValue'], storeID, request.form['ingredientID']))
    conn.commit()
    cur.close()
    return redirect('/storepage')

@app.route('/orders', methods=['POST'])
def orders():
    return redirect('/storepage')

@app.route('/customerpage', methods=['POST'])
def customerPage():
    cur = conn.cursor()
    cur.execute("SELECT s_city FROM store;")
    result = cur.fetchall()
    cur.close()
    return render_template('customerpage.html', stores = result)

@app.route('/returnHome', methods=['POST'])
def returnHome():
    return redirect('/')

@app.route('/customerlogin', methods=['POST'])
def customerLogin():
    global customerName
    global customerAddress
    global storeID
    global orderID
    customerName = request.form['cName']
    customerAddress = request.form['cAddress']
    #time = datetime.now()
    #placementTime = time.strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.cursor()
    cur.execute("SELECT s_storeID FROM store WHERE s_city = %s;", (request.form['cLocation'],))
    result = cur.fetchone()
    storeID = int(result[0])

    cur.execute("SELECT COUNT(*) FROM orders;")
    count = cur.fetchone()
    orderID = int(count[0]) + 1
    
    cur.close()
    return redirect('/pizzapage')

@app.route('/pizzapage')
def pizzaPage():
    global pizzaList
    totalPrice = 0
    for pizza in orderList:
        totalPrice += float(pizza.price)
    tPrice = '${:,.2f}'.format(totalPrice)
    return render_template('pizzapage.html', pizzas = pizzaList, total = tPrice)

@app.route('/newPizza', methods=['POST'])
def newPizza():
    global orderList
    global pizzaList
    global orderID
    
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM pizza;")
    count = cur.fetchone()
    
    pizzaID = int(count[0]) + 1 + len(orderList)
    size = request.form['size']
    toppings = request.form.getlist('toppings')
    bellPepper = 'bellPepper' in toppings
    jalapeno = 'jalapeno' in toppings
    olive = 'olive' in toppings
    pepperoni = 'pepperoni' in toppings
    pineapple = 'pineapple' in toppings
    sausage = 'sausage' in toppings
    price = 0 
    
    cur.execute("SELECT i_priceperunit FROM ingredient ORDER BY i_ingredientID ASC;")
    result = cur.fetchall()
    doughPrice = float(result[0][0])
    saucePrice = float(result[1][0])
    cheesePrice = float(result[2][0])
    bellPepperPrice = float(result[3][0])
    jalapenoPrice = float(result[4][0])
    olivePrice = float(result[5][0])
    pepperoniPrice = float(result[6][0])
    pineapplePrice = float(result[7][0])
    sausagePrice = float(result[8][0])
    cur.close()

    price += doughPrice + saucePrice + cheesePrice
    price += bellPepperPrice * bellPepper
    price += jalapenoPrice * jalapeno
    price += olivePrice * olive
    price += pepperoniPrice * pepperoni
    price += pineapplePrice * pineapple
    price += sausagePrice * sausage
    price *= 3 if size == 'L' else 2 if size == 'M' else 1
    

    myPizza = Pizza(pizzaID, orderID, size, bellPepper, jalapeno, olive, pepperoni, pineapple, sausage, price)
    orderList.append(myPizza)

    pizzaSize = 'Large' if myPizza.size == 'L' else 'Medium' if myPizza.size == 'M' else 'Small'
    pPrice = '${:,.2f}'.format(myPizza.price)
    toppings = ''
    if myPizza.bellPepper:
        toppings += 'Bell Pepper, '
    if myPizza.jalapeno:
        toppings += 'Jalapeno, '
    if myPizza.olive:
        toppings += 'Olive, '
    if myPizza.pepperoni:
        toppings += 'Pepperoni, '
    if myPizza.pineapple:
        toppings += 'Pineapple, '
    if myPizza.sausage:
        toppings += 'Sausage, '
    toppings = toppings[0:-2]
    pizzaText = "%s Pizza with %s @ %s" % (pizzaSize, toppings, pPrice)
    pizzaList.append(pizzaText)
    return redirect('/pizzapage')

@app.route('/placeOrder', methods=['POST'])
def placeOrder():
    global orderID
    global storeID
    global customerName
    global customerAddress
    global orderList
    if orderList:
        time = datetime.now()
        placementTime = time.strftime("%Y-%m-%d %H:%M:%S")
        totalPrice = 0
        for pizza in orderList:
            totalPrice += float(pizza.price)
        totalPrice = '{:,.2f}'.format(totalPrice)
        cur = conn.cursor()
        cur.execute("INSERT INTO orders VALUES (%s, %s, %s, %s, %s, %s);", (orderID, storeID, customerName, customerAddress, placementTime, totalPrice))
        for pizza in orderList:
            cur.execute("INSERT INTO pizza VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);", (pizza.pizzaID, pizza.orderID, pizza.size, pizza.bellPepper, pizza.jalapeno, pizza.olive, pizza.pepperoni, pizza.pineapple, pizza.sausage))
    
        for pizza in orderList:
            mult = 3 if pizza.size == 'L' else 2 if pizza.size == 'M' else 1
            cur.execute("UPDATE storeInventory SET si_quantity = si_quantity - (1 * %s) WHERE si_storeID = %s AND si_ingredientID <= 3;", (mult, storeID))
            if pizza.bellPepper:
                cur.execute("UPDATE storeInventory SET si_quantity = si_quantity - (1 * %s) WHERE si_storeID = %s AND si_ingredientID = 4;", (mult, storeID))
            if pizza.jalapeno:
                cur.execute("UPDATE storeInventory SET si_quantity = si_quantity - (1 * %s) WHERE si_storeID = %s AND si_ingredientID = 5;", (mult, storeID))
            if pizza.olive:
                cur.execute("UPDATE storeInventory SET si_quantity = si_quantity - (1 * %s) WHERE si_storeID = %s AND si_ingredientID = 6;", (mult, storeID))
            if pizza.pepperoni:
                cur.execute("UPDATE storeInventory SET si_quantity = si_quantity - (1 * %s) WHERE si_storeID = %s AND si_ingredientID = 7;", (mult, storeID))
            if pizza.pineapple:
                cur.execute("UPDATE storeInventory SET si_quantity = si_quantity - (1 * %s) WHERE si_storeID = %s AND si_ingredientID = 8;", (mult, storeID))
            if pizza.sausage:
                cur.execute("UPDATE storeInventory SET si_quantity = si_quantity - (1 * %s) WHERE si_storeID = %s AND si_ingredientID = 9;", (mult, storeID))
        conn.commit()
        cur.close()
        return redirect('/thankYouPage')
    else:
        return redirect('/pizzapage')

@app.route('/thankYouPage')
def thankYouPage():
    global customerName
    global customerAddress
    global pizzaList
    totalPrice = 0
    for pizza in orderList:
        totalPrice += float(pizza.price)
    tPrice = '${:,.2f}'.format(totalPrice)
    return render_template('thankyoupage.html', name = customerName, address=customerAddress, pizzas = pizzaList, total = tPrice)

@app.route('/returnToHome')
def returnToHome():
    global orderList
    global pizzaList
    orderList = []
    pizzaList = []
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask,render_template,redirect,url_for,request,jsonify,session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func,select
from datetime import datetime
from flask_cors import CORS
import sentry_sdk

from database import display_profit, Total_profit, pro_for_today, display_sum_sales, display_sum_sales_today, display_sales, day_sales, pro_per_day, get_remaining_stock_per_product, insert_sales



import os

sentry_sdk.init(
    dsn="https://803ae945357ca4dcc17c7ad8d705b95b@o4507805013573632.ingest.us.sentry.io/4507811253977088",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
)

app = Flask(__name__)


app =  Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']= 'postgresql://postgres:0777@localhost/test_api'
db = SQLAlchemy(app)




class Product(db.Model):
    __tablename__='products'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String,nullable= False)
    buying_price = db.Column(db.Integer,nullable= False)
    selling_price = db.Column(db.Integer,nullable= False)
    stock_quantity= db.Column(db.Integer,nullable= False)
    sale = db.relationship('Sale',backref='product')


class Sale(db.Model):
    __tablename__ ='sales'
    id = db.Column(db.Integer,primary_key=True)
    pid =db.Column(db.Integer,db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer,nullable= False)
    created_at = db.Column(db.DateTime,server_default = func.now())




with app.app_context():
    db.create_all()


CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5500"}})


@app.route('/product',methods=['GET','POST'])
def product():
    if request.method == 'POST':
        try:
            data = request.json
            name = data['name']
            buying_price = data['buying_price']
            selling_price = data['selling_price']
            stock_quantity = data['stock_quantity']
            product = Product(name=name,buying_price=buying_price,selling_price=selling_price,stock_quantity=stock_quantity)
            db.session.add(product)
            db.session.commit()
            return jsonify({"message":"product added successfully"}),201
        except Exception as e:
            return jsonify({'error':str(e)}),500
    elif request.method == 'GET':
        products = db.session.execute(db.select(Product).order_by(Product.name)).scalars()
        prods =[]
        for product in products:
            
            prods.append({
                "id":product.id,
                "name":product.name,
                "buying_price":product.buying_price,
                "selling_price":product.selling_price,
                "stock_quantity":product.stock_quantity

            })
        return jsonify({"products": prods}),200



@app.route('/sales',methods=['GET','POST'])
def sales():
    if request.method == 'POST':
        try:
            data = request.json
            pid = data['pid']
            quantity = data['quantity']
            sale = Sale(pid=pid,quantity=quantity)
            db.session.add(sale)
            db.session.commit()
            return jsonify({"message":"Sale made successfully"}),201
        except Exception as e:
            return jsonify({"error":str(e)}),500
    elif request.method == 'GET':
        try:
            sales = db.session.execute(db.select(Sale).order_by(Sale.pid)).scalars()
            sales_data = []
            for sale in sales:
                sales_data.append({
                    'product': sale.pid,
                    'quantity': sale.quantity,
                    'created_at': sale.created_at
                })
            return jsonify({"sales": sales_data}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route("/make_sale", methods=['POST'])
def make_sale():
    try:
        data = request.json
        pid = data['pid']
        quantity = data['quantity']

        product = Product.query.get(pid)
        if not product:
            return jsonify({"error": "Invalid product ID"}), 400

        stock = product.stock_quantity
        if quantity <= 0 or quantity > stock:
            return jsonify({"error": "Invalid quantity"}), 400

        product.stock_quantity -= quantity
        sale = Sale(pid=pid, quantity=quantity)
        db.session.add(sale)
        db.session.commit()
        return jsonify({"message": "Sale made successfully"}), 201

    except ValueError:
        return jsonify({"error": "Invalid quantity"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app. route('/dashboard',methods=['GET','POST'] )
def dashboard():

    sales_per_day = db.session. query(
    func.date(Sale.created_at). label('date'),
    func.sum(Sale.quantity * Product.selling_price). label('sales_per_day')
    ).join(Product).group_by(func.date(Sale.created_at)).all()

    profit_per_day = db. session. query(
    func.date(Sale.created_at). label('date'),
    func.sum( (Sale.quantity * Product.selling_price)-
    (Sale.quantity * Product.buying_price) ). label("profit")
    ).join(Product).group_by(func.date(Sale.created_at)).all()

    sales_data= [ {'date':str(date),"total_sales": total_sales }
    for date, total_sales in sales_per_day]
    
    profit_data = [ {'date':str(date),"total_profit": total_profit }
                   for total_profit, date in profit_per_day]
    return jsonify({"sales_data": sales_data, "profit_data": profit_data}), 200
    


    
# testing sentry  
@app.route('/sentry_error')
def hello_world():
    try:
        division_by_zero = 1 / 0
        return jsonify({"result": division_by_zero})
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return jsonify({"error":str(e)})
        
    

if __name__ == '__main__':
    app.run(debug=True)
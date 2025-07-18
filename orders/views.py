from django.shortcuts import render,redirect
from carts.models import CartItem
from .forms import OrderForm
from .models import Order,Payment,OrderProduct
import datetime
from store.models import Product
import json
from django.http import JsonResponse

#verifacation emaill
from django.template.loader import render_to_string
from django.core.mail import EmailMessage

# Create your views here.

def payments(request):
    body=json.loads(request.body)
    order=Order.objects.get(user=request.user,order_number=body['orderID'])  #,is_ordered=False
    payment=Payment(
        user=request.user,
        payment_id=body['tranID'],
        payment_method=body['payment_method'],
        amount_paid=order.order_total,
        status=body['status'],
    )
    payment.save()
    order.payment=payment
    order.is_ordered=True
    order.save()

    #move the cart items to order product table
    cart_items=CartItem.objects.filter(user=request.user)
    for item in cart_items:
        orderproduct=OrderProduct()
        orderproduct.order_id=order.id
        orderproduct.payment=payment
        orderproduct.user_id=request.user.id
        orderproduct.product_id=item.product_id
        orderproduct.quantity=item.quantity
        orderproduct.product_price=item.product.price
        orderproduct.ordered=True
        orderproduct.save()

        cart_item=CartItem.objects.get(id=item.id)
        product_varation=cart_item.variations.all()
        orderproduct=OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variations.set(product_varation)
        orderproduct.save()

        #reduce the quantity of sold products
        product=Product.objects.get(id=item.product_id)
        product.stock-=item.quantity
        product.save()

    #clear the cart
    CartItem.objects.filter(user=request.user).delete()

    #send order recive email to customer
    mail_subject='Thank you for your order!'
    message=render_to_string('orders/order_recieved_email.html',{
        'user':request.user,
        'order':order,
    })
    to_email=request.user.email
    send_email=EmailMessage(mail_subject,message,to=[to_email])
    send_email.send()

    #send order number and transaction id back to senddata method via JsonRespones
    data={
        'order_number':order.order_number,
        'tranID':payment.payment_id,
    }
    return JsonResponse(data)


def place_order(request,total=0,quantity=0):
    current_user=request.user

    #if cart is zero redirect to store
    cart_items=CartItem.objects.filter(user=current_user)
    cart_count=cart_items.count()
    if not cart_count:
        return redirect('store')

    grand_total=0
    tax=0
    for cart_item in cart_items:
        total+=(cart_item.product.price* cart_item.quantity)
        quantity+=cart_item.quantity
    tax=(2*total)/100
    grand_total=total+tax

    if request.method=='POST':
        form=OrderForm(request.POST)
        if form.is_valid():
            #store all the bulling info
            data=Order()
            data.user=current_user
            data.first_name=form.cleaned_data['first_name']
            data.last_name=form.cleaned_data['last_name']
            data.phone=form.cleaned_data['phone']
            data.email=form.cleaned_data['email']
            data.address_line_1=form.cleaned_data['address_line_1']
            data.address_line_2=form.cleaned_data['address_line_2']
            data.country=form.cleaned_data['country']
            data.state=form.cleaned_data['state']
            data.city=form.cleaned_data['city']
            data.order_note=form.cleaned_data['order_note']
            data.order_total=grand_total
            data.tax=tax
            data.ip=request.META.get('REMOTE_ADDR')
            data.save()

            #Generate order number
            yr=int(datetime.date.today().strftime('%Y'))
            dt=int(datetime.date.today().strftime('%d'))
            mt=int(datetime.date.today().strftime('%m'))
            d=datetime.date(yr,mt,dt)
            current_date=d.strftime('%Y%m%d')
            order_number=current_date+str(data.id)
            data.order_number=order_number
            data.save()
            usd_total = round(grand_total / 83.0, 2)
            order=Order.objects.get(user=current_user,is_ordered=False,order_number=order_number)
            context={
                'order':order,
                'cart_items':cart_items,
                'total':total,
                'tax':tax,
                'grand_total':grand_total,
                'usd_total':usd_total,
            }
            return render(request,'orders/payments.html',context)
    else:
        return redirect('checkout')


def order_complete(request):
    order_number=request.GET.get('order_number')
    tranID=request.GET.get('payment_id') 
    try:
        order=Order.objects.get(order_number=order_number,is_ordered=True)
        ordered_products=OrderProduct.objects.filter(order_id=order.id)
        sub_total=0
        for i in ordered_products:
            sub_total+=i.product_price*i.quantity

        payment=Payment.objects.get(payment_id=tranID)

        context={
            'order':order,
            'ordered_products':ordered_products,
            'order_number':order.order_number,
            'tranID':payment.payment_id,
            'payment':payment,
            'sub_total':sub_total,
        }
        return render(request,'orders/order_complete.html',context)
    except (Payment.DoesNotExist,Order.DoesNotExist):
        return redirect('home')
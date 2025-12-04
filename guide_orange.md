Getting Started : 
The Orange Money Web Payment API DEV (Sandbox) allows web merchants to 
integrate Orange Money as means of payment in their website. Orange Money is a 
mobile payment solution across 17 countries in Africa and the Middle East. 
• The Web Payment Sandbox is a E2E platform created for partners’ integration 
and testing. 
• Orange Money tests accounts (Merchant and Subscribers) are available to 
perform payment transactions. 
• Integration Tools: USSD simulator and OM Payment Add-on (page) 
Steps of test: 
1. subscription via Orange Partner portal 
2. access_token generation 
3. Web Payment API 
4. Transactions Status API 
Watch the video below and see how you can use our API to offer Orange Money 
payment solution on your e-commerce website. 
video 
1- Web Payment Offer subscription - Getting My Merchant Key 
You have been invited to subscribe the Orange Money Web Payment API. You are about 
to use your merchant wallet in a secure way to offer a new payment method to your 
customers. 
1.1 Application creation 
https://developer.orange.com/myapps 
1.2 'Orange Money WebPayDev' API addition 
You should have received an email with Channel User and subscriber identifiers: 
Channel User: 
• id/login/name: MerchantWP00100 
• Merchant Account Number: 7701900100 
• Merchant Code: 101021 
• PIN code: xxxx 
Subscriber: 
• MSISDN: 7701100100 
• PIN: xxxx 
If it is not the case, please ask it by email to: 
• georgiana.cruceru@orange.com 
So, add the API Orange Money Web Pay Dev to your Application and let's generate your 
Merchant Key by entering your Merchant Account Number (channel user 
MSISDN) and Merchant Code 
Warning: Orange Money WebPay offers are hidden. You must have been invited to see 
them. The Merchant Key will be created in the system only if you provide a valid Orange 
Money account and if you have proper rights to subscribe the service. If you do not know 
your Merchant Code, please contact your local Orange Money support team. 
IMPORTANT: The Merchant key will be used as Orange Money account 
identifier for all payments transactions (no MSISDN, nor PIN will not be 
required in the API). Please write down your Merchant Key and store it in 
a safe place. 
Note that a single application can be subscribed to a DEV offer and a single country. For 
a second country, you need to create a new application. 
2. Get your Access token 
Legged OAuth2.0 proxy V3 - Orange Developer 
Warning: Check you are using the right URL: /orange-money
webpay/dev/v1/webpayment HTTP/1.1 
NOTE: The access_token is valid for the duration, in seconds, specified by expires_in. 
Therefore, you do not need to request a new access token as your client application 
doesn't receive an error indicating that your access token expired. At the present time, 
access_token have a lifetime of about 90 days. 
If your token is expired, you just have to get a new token by the same method. 
You can get more details about token here. 
3. Web Payment API 
This API allows you to create a payment session in the Orange Money system. A 
payment transaction will be created based on the information provided in your request 
and a Payment Token will be returned in the API response. 
3.1 Web Payment request 
3.1.1 Web Payment transaction initialization 
You have to send a post in HTTPS : 
https://api.orange.com/orange-money-webpay/dev/v1/webpayment 
 
Authorization: Bearer IW3gdUVOvQVcO7mGNsOZgwdhDNvE 
Accept: application/json 
Content-Type: application/json 
{ 
  "merchant_key": "a86b2087", 
  "currency": "OUV", 
  "order_id": "MY_ORDER_ID_08082105_0023457", 
  "amount": 1200, 
  "return_url": "http://myvirtualshop.webnode.es", 
  "cancel_url": "http://myvirtualshop.webnode.es/txncncld/", 
  "notif_url": "http://www.merchant-example2.org/notif", 
  "lang": "fr" 
  "reference": "ref Merchant" 
} 
Content-Type: application/json 
 
{ 
   "status":201, 
   "message":"OK", 
   "pay_token":"f5720dd906203c62033ffe64ed75614785878b0ab2231d9c582b2908fca0ab9a", 
   "payment_url":"https:\/\/webpayment-qualif.orange-money.com\/payment\/pay_token
 \/f5720dd906203c62033ffe64ed75614785878b0ab2231d9c582b2908fca0ab9a", 
   "notif_token":"dd497bda3b250e536186fc0663f32f40" 
} 
Warning : On API DEV we use OUV as currency. On API country is the country 
currency. 
Note that the field ''order_id'' must be unique for the system. 
The fields order_id and reference are limited to 30 chars and return_url, cancel_url 
and notify_url to 120 chars 
The field reference refers to the merchant name 
You can find below an example of the code for a postman request: 
POST /orange-money-webpay/dev/v1/webpayment HTTP/1.1 
Host: api.orange.com 
Content-Type: application/json 
Authorization: Bearer R5EVAffaxgpTojhuTorBSU1qMHgy 
Accept: application/json 
Cache-Control: no-cache 
Postman-Token: e18f3aac-9bd7-ddc5-a3a4-668e6089a0d5 
 
{ 
  "merchant_key": "ad8b9717", 
  "currency": "OUV", 
  "order_id": "TestOPE_001903", 
  "amount": 1500, 
  "return_url": "https://www.merchant-example.org/return", 
  "cancel_url": "https://www.merchant-example.org/cancel", 
  "notif_url": "https://www.merchant-example.org/notif", 
  "lang": "fr", 
  "reference": "ref Merchant" 
} 
OK! Now, all that you need is to redirect your client to our secured payment 
page: https://webpayment-ow-sb.orange
money.com/payment/pay_token/a4b2a348ee580b0d21fd3b2b9d67e1aeca739a28ca6d6
 0d99f1bc833b8ffb909 
 
In order to ask for an OTP code and confirm your transaction, you can use the Sandbox 
Simulator. 
Once the transaction is confirmed by the Orange client, the system will redirect the user 
to your return_url. Then, a HTTP notification will be posted to the notif_urlyou sent in 
the web payment request. 
 
 
 
3.1.2 Web Payment request URLs 
There is 3 urls in the webpayment request: 
• return_url: the url of the web site where the customer will return when the 
payment will be finished and the customer decide to click on the return link of the 
web payment web site 
• cancel_url: the url of the web site where the customer will return when the 
payment will be canceled by the customer by clicking on the cancel link of the 
web payment web site 
• notif_url: the notification url used by the webpayment backend to notify the 
merchant backend of the status of the payment’s transaction (see more details at 
“Transaction Notification”). This notification is only sent when the payment 
process is confirmed and when it ends with a ‘SUCCESS’ or ‘FAILED’ status 
These urls are sent in the body of the webpayment request, so the merchant can use 
dynamics urls that depends on the merchant web site context (e.g. with url parameters 
like “&returnOnCart=1”, “&referrer=site1.com”). 
One WebPayment account can be used to centralize the merchant money of multiple 
web sites by putting the same credentials/merchant_key in the requests sent to the 
WebPayment backend. Because the webpayment request urls parameters are 
dynamically set during the build of the body of the request, each web site can use its own 
URLs. 
Example: 
mywebsite1.com 
• POST https://api.orange.com/orange-money-webpay/dev/v1/webpayment – 
• Bearer IW3gdUVOvQVcO7mGNsOZgwdhDNvE 
• "merchant_key": "a86b2087" 
• “return_url”: “mywebsite1.com/webpayment_returnurl_1” 
• “cancel_url” : “mywebsite1.com/webpayment_cancelurl_1” 
• “notif_url” : “mywebsite1.com/webpayment_notifurl_1” 
mywebsite2.com 
• POST https://api.orange.com/orange-money-webpay/dev/v1/webpayment – 
• Bearer IW3gdUVOvQVcO7mGNsOZgwdhDNvE 
• "merchant_key": "a86b2087" 
• “return_url”: “mywebsite1.com/webpayment_returnurl_2” 
• “cancel_url” : “mywebsite1.com/webpayment_cancelurl_2” 
• “notif_url” : “mywebsite1.com/webpayment_notifurl_2” 
3.2 OTP code getting (via Partner USSD Sandbox Simulator) 
The Partner Sandbox simulator is a Web based interface allowing partners and 
developers to perform the following transactions in the Sandbox environment: 
• OTP request 
• Merchant Balance request 
• Subscriber Balance request 
You can access the Simulator: https://mpayment.orange-money.com/mpayment-otp/login  
You can login with the merchant account provided for the Sandbox (login: Merchant 
Account Number, password: channel user Id). 
Then you can request for an OTP with the subscriber PIN code. 
You just have to fill the OTP code in the payment page, and click on “Confirmer”: 
Once MSISDN and OTP are filled in the payment page, click on “Confirmer”: 
… and the HTTPS notification is posted to the notif_url you sent in the web payment 
request. 
Warning: make sure you have implemented the notif_url to have visibility on 
payment status, if not you will not be able to validate in real time the order and 
change its status on your database 
3.3 Transaction Notification 
The client has confirmed the transaction! Orange Money has just sent the Payment 
Notification to your notif_url 
POST http://www.merchant-example2.org/notif     
{ 
"status":"SUCCESS", 
"notif_token":"dd497bda3b250e536186fc0663f32f40", 
"txnid": "MP150709.1341.A00073" 
} 
Warning: Do you remember the notif_token present in the web payment 
response? Make sure this token matches the token sent in the notification POST. 
This way, you will validate the authenticity of the notification. 
4. Transactions Status API 
In addition of Transaction Notification, you can use the Transaction Status API that 
allows you to consult in real time the current status of a payment. In practice, this can be 
useful for cases where notification are not sent (e.g. when users don’t validate their 
payments) 
https://api.orange.com/orange-money-webpay/dev/v1/transactionstatus 
Accept: application/json 
Authorization: Bearer WI9VmGXfNB38s1e6A26Hob19AP2c 
Content-Type: application/json 
{ 
   "order_id": "MY_ORDER_ID_08082105_0023457", 
   "amount": 1200, 
   "pay_token": "f5720dd906203c62033ffe64ed75614785878b0ab2231d9c582b2908fca0ab9a" 
} 
201 Created 
Content-Type:  application/json; charset=utf-8 
 
{ 
   "status": "SUCCESS", 
   "order_id": "MY_ORDER_ID_08082105_0023457", 
   "txnid": "MP150709.1341.A00073" 
} 
The status could take one of the following values: INITIATED; PENDING; 
EXPIRED; SUCCESS; FAILED 
• INITIATED waiting for user entry 
• PENDING user has clicked on “Confirmer”, transaction is in progress on Orange 
side 
• EXPIRED user has clicked on “Confirmer” too late (after token’s validity) 
• SUCCESS payment is done 
• FAILED payment has failed 
If the transaction is not tried (the customer doesn’t do anything, or returns on Merchant 
site), status stays on INITIATED state. By default, the the token’s validity is 10 minutes. 
The passage from PENDING state to SUCCESS or FAILED state is rapid. 
5. API reference 
You can find the API description with more details and error codes on the API reference. 
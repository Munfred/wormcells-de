from flask import Flask,  jsonify, request, render_template
import logging
import pandas as pd
import sys
import json
import time
import boto3
import decouple
from io import StringIO
import urllib

logging.basicConfig(level=logging.DEBUG)

flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return render_template("index.html")

@flask_app.route('/submit', methods=['POST', 'GET'])
def receive_submission():
    print('buuu')
    # answer is a dict of json strings containing selected row and column index numbers
    answer = request.form.to_dict(flat=False)
    print(answer)

    # need to convert the json strings to stringio, then to a data frame
    # data1 is the selection for the first group, data2 for the second

    # print(email)

    data1 = StringIO(json.loads(answer['data1'][0]))
    # print(data1)
    group1_df = pd.read_csv(data1, names=['cell_type1', 'experiment1'])
    # print(data1_df)

    data2 = StringIO(json.loads(answer['data2'][0]))
    group2_df = pd.read_csv(data2, names=['cell_type2', 'experiment2'])

    genes = StringIO(json.loads(answer['genes'][0]))
    genes_df = pd.read_csv(genes, names=['selected_genes'])
    print(genes_df)

    # now map the index number to experiment name and cell type name


    email = answer['email'][0].strip()
    print(email)

    timestr = time.strftime("%Y%m%d-%H%M%S")
    print(timestr)

    s3filename = 'submissions/' + email + '%' + timestr + '.csv'

    selected_groups_df = pd.concat([group1_df, group2_df, genes_df], axis=1)
    print(selected_groups_df)
    AWS_S3_ACCESS_KEY = decouple.config('AWS_S3_ACCESS_KEY')
    AWS_S3_SECRET = decouple.config('AWS_S3_SECRET')
    sendgrid_key = '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'
    sendgrid_name = 'scvi_de_wormbase'

    csv_buffer = StringIO()
    selected_groups_df.to_csv(csv_buffer)

    client = boto3.client('s3',
                          aws_access_key_id=AWS_S3_ACCESS_KEY,
                          aws_secret_access_key=AWS_S3_SECRET
                          )
    # client.put_object(
    #     Body=csv_buffer.getvalue(),
    #     Bucket='scvi-differential-expression',
    #     Key=s3filename,
    #     ACL='public-read'
    # )
    url = 'https://scvi-differential-expression.s3.us-east-2.amazonaws.com/' + urllib.parse.quote(s3filename)
    print('the objeoct has been put')
    print(s3filename)
    print()

    ec2 = boto3.resource('ec2')
    user_data = '''#!/bin/bash
wget https://github.com/Munfred/wormcells-de/blob/master/scvi_de.py    
python3 scvi_de.py ''' + url + ' ' + AWS_S3_ACCESS_KEY + ' ' + AWS_S3_SECRET + ' ' + sendgrid_key + ' ' + sendgrid_name + ''' ;
echo "sudo halt" '''

    print(user_data)

    # create a new EC2 instance
    # instances = ec2.create_instances(
    #     ImageId='ami-032240eb155129553',
    #     MinCount=1,
    #     MaxCount=1,
    #     InstanceType='t2.micro',
    #     UserData=user_data,
    #     KeyName='ec2-keypair'
    # )
    #
    # print('the instance has been created')


    return 'derpderp'
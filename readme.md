# wormcells-de

`wormcells-de` is a flask app that allows users to perform differential expression (DE) on single cell RNA sequencing data (scRNA-seq). Users can select cells to compare on a web interface, and submissions cause the spawn of a dedicated EC2 instance for computing the DE. In this deployment instances are configured to have 64GB RAM, allowing results to be emailed to users in less than 5 minutes.

To perform differential expression we use [scVI ](https://scvi.readthedocs.io/en/stable/index.html) v0.6.3. The method for performing differential expression is the change option introduced in scVI v0.6.0 and described in [Boyeau et al, bioRxiv 2019 ](https://doi.org/10.1101/794289). It consists in estimating an effect size random variable (here, log2 fold-change) and performing Bayesian hypothesis testing on this variable.

A Python tutorial using Jupyter Notebooks on how to reproduce this analysis using the Packer 2019 dataset is [available on the official scVI documentation ](https://scvi.readthedocs.io/en/stable/contributed_tutorials/scVI_DE_worm.html). The code used to run the wormcells-de app is available at the [wormcells-de GitHub repository](https://github.com/Munfred/wormcells-de). The data for Packer 2019, Taylor 2019 and Cao 2017 is [available on GitHub as an anndata file ](https://github.com/Munfred/wormcells-site/releases/tag/Packer2019Taylor2019Cao2019_wrangle2)(1GB size).



## Deployment steps

*Warning: these steps are not comprehensive, since it was mostly written down as a reminder for myself. Deployment for a different dataset can be done, but requires changes in several places. If you think deploying this would be useful for your work, let me know. *

Production deployment is done following this guide from Digital Ocean: 
https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04

It is run with `gunicorn --bind 0.0.0.0:5000 wsgi:flask_app`

`flask_app` is the app name inside `app.py`

### Setting up a new server instance with Ubuntu 18.04

```
sudo apt update -y
sudo apt install python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools -y
sudo apt install python3-venv -y

cd ~
git clone https://github.com/Munfred/wormcells-de.git
cd wormcells-de
python3.6 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install wheel
pip install gunicorn flask

gunicorn --bind 0.0.0.0:5000 wsgi:flask_app
deactivate
```

#### Configuring service
Then, following the the tutorial, create service file 
```
sudo nano /etc/systemd/system/wormcells.service
```
Contents:

```
[Unit]
Description=Gunicorn instance to serve wormcells
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/wormcells-de/
Environment="PATH=/home/ubuntu/wormcells-de/venv/bin"
ExecStart=/home/ubuntu/wormcells-de/venv/bin/gunicorn --workers 5 --bind unix:wormcells.sock -m 007 wsgi:flask_app

[Install]
WantedBy=multi-user.target
```

Then
```
sudo systemctl start wormcells
sudo systemctl enable wormcells
```

#### Configuring Nginx

Install Nginx, create server block configuration file:
```
sudo apt install nginx -y

sudo nano /etc/nginx/sites-available/wormcells
```

Contents:
```
server {
    listen 80;
    server_name wormcells de.wormcells.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/wormcells-de/wormcells.sock;
    }
}
```


To enable the Nginx server block configuration link the file to the sites-enabled directory:

```
sudo ln -s /etc/nginx/sites-available/wormcells /etc/nginx/sites-enabled
```
With the file in that directory, you can test for syntax errors:
```
sudo nginx -t
```

If this returns without indicating any issues, restart the Nginx process to read the new configuration:

** MAKE SURE NOTHING ELSE IS RUNNING ON PORT 80 **
```
sudo systemctl restart nginx
```

## Configuring the ec2 image (which runs scVI)

The image needs to have the trained autoencoder, the adata file, and the dependencies in place. 

If the VAE or data are updated, change the wget urls
```
cd ~
wget https://github.com/Munfred/wormcells-site/releases/download/cao2017packer2019taylor2019/cao2017packer2019taylor2019.h5ad &&
wget https://github.com/Munfred/wormcells-de/releases/download/cpt_vae_v2/cpt_vae_v2.pkl &&
sudo apt-get update &&
sudo apt install python3-pip -y &&
sudo apt install python3.7 -y &&
python3.7 -m pip install pip &&
python3.7 -m pip install scvi plotly sendgrid boto3
```

# Modify settings.py to remove debug mode
sed -i "s/DEBUG.*$/DEBUG\ =\ False/g" ../grb/project/settings.py

# Modify settings.py to allow connections from all IPs
sed -i "s/ALLOWED_HOSTS.*$/ALLOWED_HOSTS\ =\ ['\*']/g" ../grb/project/settings.py

# Apply migrations
python ../grb/manage.py makemigrations project
python ../grb/manage.py migrate project
python ../grb/manage.py makemigrations
python ../grb/manage.py migrate

# Seed database (TODO)

# Run server allowing for traffic on port 8000
# Using port 80 requires using sudo, which somehow has a different PYTHONPATH
# and this is frankly too tricky for a port difference right now
python ../grb/manage.py runserver
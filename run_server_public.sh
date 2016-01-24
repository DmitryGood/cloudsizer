#!/bin/bash
env DATABASE_URL=mysql://cloudcalc:cloudcalc@localhost/cloudcalc python manage.py run_public

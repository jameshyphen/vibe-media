# Vibe media

## Description
A social media app written in Django by using Windusrf, trying out vibe coding.

### How to run

This project was built based on python3.12

1. **Create a Python virtual environment**

   Run the following command to create a virtual environment:
   ```bash
   python3.12 -m venv venv
   ```

2. **Activate the virtual environment**

   ```bash
   source venv/bin/activate
   ```

3. **Install dependencies**

   Install the required Python packages using `pip`:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run Docker Compose**

   This project is using postgres which we create with docker compose:
   ```bash
   docker-compose up -d
   ```

4. **Apply database migrations**

   Run the following command to apply migrations:
   ```bash
   python manage.py migrate
   ```

5. **Run the development server**

   Start the Django development server:
   ```bash
   python manage.py runserver
   ```

6. **Access the application**

   Open your browser and go to:
   ```
   http://127.0.0.1:8000/
   ```

### Deployments

This project is deployed with ArgoCD & k8s
Find the deploy repository here: https://github.com/jameshyphen/vibe-media-deploy
# Deploying VisionInspect AI

The repository includes a Render Blueprint for the web app, API, PostgreSQL
database, and persistent image uploads. The API runs the CPU version of PyTorch;
model inference will be slower than on a GPU.

## Deploy with Render

1. Push the project to a GitHub repository that your Render account can access.
   Make sure the `ml` model files are included in the repository.
2. In the [Render Dashboard](https://dashboard.render.com/), choose **New** >
   **Blueprint** and connect that repository.
3. When Render asks for `FRONTEND_URL`, enter:
   `https://visioninspectai-frontend.onrender.com`
4. Review the Blueprint resources and deploy them. The API uses a paid Starter
   web service and a 1 GB persistent disk; Render's current prices and database
   plan availability are shown in the dashboard before confirmation.
5. Wait for both web services and the database to finish deploying. Open
   `https://visioninspectai-frontend.onrender.com` to share the app with your
   mentor. The API health endpoint is
   `https://visioninspectai-api.onrender.com/health`.

If Render reports that either service name is already taken, change the
corresponding `name` in `render.yaml`. Also update the frontend URL entered for
`FRONTEND_URL` and the API URL returned by the Blueprint as needed.

## After deployment

- Create an account in the deployed app and test login and image inspection.
- The `visioninspectai-uploads` disk keeps uploaded images across deploys.
- Keep `JWT_SECRET_KEY` and `DATABASE_URL` in Render's environment settings;
  never commit production secrets to Git.
- CPU model inference can be slow. The first deploy also installs PyTorch and
  the ML packages and may take several minutes.

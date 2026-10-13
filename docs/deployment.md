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

## Deploying the frontend on Vercel

If the frontend is hosted separately on Vercel, set `VITE_API_URL` in the
Vercel project's environment variables to the API service origin (for example,
`https://visioninspectai-api.onrender.com`, without a path), then redeploy the
frontend. Set the API service's `FRONTEND_URL` to the exact Vercel site origin
so the browser's API requests are allowed by CORS. Redeploy the API after
changing its environment variables.

For the current deployment, the Vercel frontend uses
`https://visioninspectai-backend-e7lw.onrender.com` as its API origin, and its
site origin is `https://vision-inspect-ai-mauve-seven.vercel.app`. Confirm
these match the `VITE_API_URL` and `FRONTEND_URL` values in the respective
hosting dashboards. If the API's `/health` endpoint returns Render's
`no-deploy` error, deploy the backend service before testing inspections.

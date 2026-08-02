# Deploying Clip.web — Vercel (frontend) + Fly.io (backend)

This file contains the exact steps you need to perform after I open the pull request. Follow them in order.

1) Create a Fly account and an app
- Sign up at https://fly.io and create a free account.
- Create a new app for the backend (you can use the default options). Note the app name (we will call this the Fly app name).

2) Create a Fly API token
- In the Fly dashboard: Account → Tokens → Create Token
- Copy the token value.

3) Add GitHub repository secrets
- Go to your GitHub repo → Settings → Secrets & variables → Actions → New repository secret
- Add the following secrets (paste exact values you obtained above):
  - FLY_API_TOKEN       -> your Fly API token
  - FLY_APP_NAME        -> your Fly app name (the app you created)

4) Merge the PR I create (mvp/auto-clipper)
- After you merge, the GitHub Actions workflow will run and deploy the backend to Fly.
- Check the Actions tab for the deploy workflow run; if successful, Fly will report the public URL for your backend.

5) Deploy the frontend to Vercel
- Go to https://vercel.com and sign up or log in.
- Click "Import Project" and pick your GitHub repository.
- Vercel will detect the Next.js frontend and provide build settings; accept the defaults.
- After initial deploy, set an environment variable in Vercel:
  - NEXT_PUBLIC_BACKEND_URL = https://<your-fly-app>.fly.dev  (replace with the Fly public URL)
- Trigger a redeploy in Vercel (it will pick up the env var) and your frontend will be live.

6) Test the site
- Open your Vercel frontend URL (example: https://your-frontend.vercel.app)
- Use the UI to upload a VOD or paste a YouTube/Twitch link. The backend (on Fly) will download/process and return a clip URL.

If you want, I can also add a GitHub Actions workflow to automatically set NEXT_PUBLIC_BACKEND_URL in Vercel via the Vercel API — but that requires a Vercel token (optional).

Troubleshooting
- If the deploy job fails, open Actions → the deploy-backend-fly workflow run and paste the logs here and I will help fix them.
- If the frontend cannot reach the backend, confirm NEXT_PUBLIC_BACKEND_URL is set correctly in Vercel and that the Fly app is responding.

If you want me to proceed now, confirm and I will push the branch and open the PR with these changes.
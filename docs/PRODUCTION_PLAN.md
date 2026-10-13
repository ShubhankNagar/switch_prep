# Go-live checklist: putting SwitchPrep on the internet for free

This is a to-do list. Work from top to bottom and tick each box. You do not need any deployment experience:
every step says where to click, what to type, and what you should see afterwards.

- **Cost:** nothing. No step asks for a payment card. If a site asks for one, stop: you have taken a wrong turn.
- **Time:** about an hour and a half, mostly waiting.
- **The code is already written.** It is on the branch `feat/shubhank`. Your job is to publish it and create
  three free accounts.

Website buttons get renamed now and then. If a label is slightly different from what is written here, look for
the closest match.

---

## Part 0: understand what you are setting up (5 minutes of reading)

The site has three parts, and each lives on a different free service:

| Part | What it is | Where it will live | Why there |
|---|---|---|---|
| The **site** | The pages people see | **GitHub Pages** | Free, always on, and the repo is already on GitHub |
| The **API** | The Java (Spring Boot) program that saves progress | **Render** | Runs our Java program for free |
| The **database** | Where progress is stored | **TiDB Cloud** | Free and works like MySQL, which the API already speaks |

A fourth piece, **Google sign-in**, is not hosted anywhere. You only register the site with Google so that
Google's "Sign in" button is allowed to appear on it.

How they talk to each other:

```
 A visitor's browser
        |
        |  loads the pages from
        v
   GitHub Pages  (the site)
        |
        |  when someone signs in or ticks something, the site calls
        v
     Render  (the API)
        |
        |  which reads and writes
        v
   TiDB Cloud  (the database)
```

Two things to know before you start:

1. **The site works even without the API.** After Part 2 the site is public and fully usable; progress is saved
   in each visitor's own browser. Parts 3 to 6 only add "sign in and see my progress on any device".
2. **The free API goes to sleep** after 15 minutes with no visitors and takes a minute or more to wake up. That is
   normal. While it wakes, the site shows "Waking sync server…" and keeps working; nothing is lost.

### Words used in this guide

| Word | Meaning |
|---|---|
| **Repository (repo)** | The project's folder on GitHub: `github.com/raj-alpha-swain/switch_prep` |
| **Owner** | The GitHub account the repo belongs to. Here that is your partner, `raj-alpha-swain` |
| **Branch** | A separate line of work. `main` is the official one; `feat/shubhank` holds the new changes |
| **Pull request (PR)** | A request to copy the changes from one branch into `main` |
| **Environment variable** | A named setting you give to a program from outside, such as a password, so it is not written in the code |
| **Origin** | The first part of a web address, up to the domain: `https://raj-alpha-swain.github.io`. No path, no slash at the end |
| **Client ID** | A long public name Google gives your site, ending in `.apps.googleusercontent.com` |

### Who must do what

Some steps can only be done by the repo's **owner** (your partner), because they change the repo's settings.
Those steps are marked **[OWNER]**. The simplest way through is to sit together, or for your partner to make you
an admin first:

- [ ] **[OWNER]** On GitHub: repo **Settings > Collaborators > Add people**, add your GitHub username. You
      accept the invitation from your email.

Being a collaborator lets you push code. Steps marked **[OWNER]** still need your partner's account.

### Keep a notes file

You will collect five values. Open a text file **outside the project folder** (so it can never be committed) and
paste this in. Fill it as you go.

```
1. Google client ID      :
2. Database host         :
3. Database user name    :
4. Database password     :
5. API address           :
```

Treat number 4 like any password: do not put it in the code, in a chat, or on GitHub.

---

## Part 1: publish the code to `main` (15 minutes)

Right now the new code exists only on your laptop. This part sends it to GitHub and merges it.

- [ ] **1.1 Look at what changed.** In a terminal:
      ```bash
      cd ~/"Shubhank Codes/Learning website/switch_prep"
      git status
      ```
      You should see a list of modified and new files and, at the top, `On branch feat/shubhank`.

- [ ] **1.2 Save the changes into git (a "commit").**
      ```bash
      git add -A
      git commit -m "Add Google sign-in, production profile and free deployment setup"
      ```
      (You can also ask Claude to do the commit for you.)

- [ ] **1.3 Send the branch to GitHub.**
      ```bash
      git push -u origin feat/shubhank
      ```
      If this says "permission denied", the collaborator invitation from Part 0 has not been accepted yet.

- [ ] **1.4 Open a pull request.** Go to `https://github.com/raj-alpha-swain/switch_prep`. GitHub shows a yellow
      bar "feat/shubhank had recent pushes" with a button **Compare & pull request**. Click it, then
      **Create pull request**.

- [ ] **1.5 Wait for the checks.** On the pull request page, a section near the bottom lists checks called
      "backend" and "frontend". They take a few minutes. Wait for green ticks.
      - If one shows a red cross, click **Details**, copy the error, and ask Claude. Do not merge.

- [ ] **1.6 Merge.** Click **Merge pull request**, then **Confirm merge**.

**You are done with Part 1 when:** the repo's front page on GitHub, on branch `main`, shows a file called
`render.yaml`.

---

## Part 2: put the site online with GitHub Pages (5 minutes)

- [ ] **2.1 [OWNER] Turn Pages on.** Repo **Settings** (top menu) **> Pages** (left menu). Under "Build and
      deployment", set **Source** to **GitHub Actions**.

- [ ] **2.2 [OWNER] Start the first deployment.** Top menu **Actions**. In the left list click
      **Deploy frontend to GitHub Pages**. On the right click **Run workflow**, keep branch `main`, click the
      green **Run workflow** button.

- [ ] **2.3 Wait** about two minutes until the run shows a green tick. (Refresh the page if nothing appears.)

- [ ] **2.4 Open the site:** <https://raj-alpha-swain.github.io/switch_prep/>

**You are done with Part 2 when:** the SwitchPrep dashboard loads at that address. Click around: open a DSA
problem, tick it, reload, and the tick is still there.

At this point the site is live. The top right says "Browser mode", which is correct: there is no sign-in yet.
You can share the link already. The remaining parts add sign-in.

---

## Part 3: register the site with Google (20 minutes)

This gives you value 1, the **Google client ID**.

- [ ] **3.1** Go to <https://console.cloud.google.com/> and sign in with a Google account. Use one that you and
      your partner are happy to have as the site's contact address. Accept the terms if asked.

- [ ] **3.2 Create a project.** At the very top, click the project picker (it may say "Select a project"), then
      **New project**. Name it `SwitchPrep`. Click **Create**, wait a few seconds, then select it in the same
      picker.

- [ ] **3.3 Open the sign-in settings.** In the search bar at the top type `Google Auth Platform` and open it.
      Click **Get started**.

- [ ] **3.4 Fill in the short form.**
      - App name: `SwitchPrep`
      - User support email: pick your email
      - Audience: **External** (this means "people outside my organisation", which is everyone)
      - Contact information: your email
      - Tick the agreement box, then **Create**.

- [ ] **3.5 Add the site's details.** In the left menu click **Branding** and fill in:
      - Application home page: `https://raj-alpha-swain.github.io/switch_prep/`
      - Application privacy policy link: `https://raj-alpha-swain.github.io/switch_prep/privacy.html`
      - Authorised domains, **Add domain**: `raj-alpha-swain.github.io`
      - **Do not upload a logo.** With a logo, Google wants to review the app first, which takes days. Without
        one, no review is needed.
      - Click **Save**.

- [ ] **3.6 Create the client.** Left menu **Clients > Create client**.
      - Application type: **Web application**
      - Name: `SwitchPrep web`
      - Under **Authorised JavaScript origins** click **Add URI** three times and enter, exactly:
        - `https://raj-alpha-swain.github.io`
        - `http://localhost`
        - `http://localhost:4200`
      - Leave **Authorised redirect URIs** empty.
      - Click **Create**.

- [ ] **3.7 Copy the Client ID** from the box that appears into your notes file as value 1. It looks like
      `1234567890-abcdefg.apps.googleusercontent.com`. Ignore the "client secret"; this site does not use it.

- [ ] **3.8 Open sign-in to everyone.** Left menu **Audience**. Under "Publishing status" click **Publish app**
      and confirm. It should now say **In production**.
      - If you skip this, only people you list by hand can sign in, and they are signed out every week.

- [ ] **3.9 Read the privacy page.** Open
      <https://raj-alpha-swain.github.io/switch_prep/privacy.html>. It tells visitors what the site stores about
      them, in your and your partner's names. If anything in it is wrong for you, tell Claude what to change
      before going further.

**You are done with Part 3 when:** value 1 is in your notes file and the Audience page says "In production".

> Common mistake: a slash at the end of an origin (`https://raj-alpha-swain.github.io/`) or adding
> `/switch_prep`. Google rejects sign-in with "origin not allowed". The origin has no path and no final slash.

---

## Part 4: create the database (15 minutes)

This gives you values 2, 3 and 4.

- [ ] **4.1** Go to <https://tidbcloud.com/> and click **Sign up**. Signing up with your Google or GitHub account
      is quickest. No card is asked for.

- [ ] **4.2 Create the database server.** You are offered to create an instance (a "cluster"). Choose:
      - Plan: **Starter** (the free one)
      - Cloud provider: **AWS**
      - Region: **Singapore** if it is in the list; otherwise the one nearest to India
      - Name: `switchprep`
      - Click **Create**. It takes under a minute.

- [ ] **4.3 Get the connection details.** Open the instance and click **Connect** (top right). In the window:
      - Connection type: **Public**
      - Connect with: **General**

- [ ] **4.4 Make the password.** Click **Generate password**. **Copy it into your notes file now** as value 4;
      it is shown only once. (If you lose it, **Reset password** in the same window makes a new one.)

- [ ] **4.5 Copy the rest** from the same window into your notes file:
      - **Host** (value 2): looks like `gateway01.ap-southeast-1.prod.aws.tidbcloud.com`
      - **User name** (value 3): looks like `3xAmPle.root`. Copy all of it, including the part before the dot.
      - The port is `4000`; you do not need to write it down.

- [ ] **4.6 Create an empty database inside the server.** Close the window. In the left menu open **SQL Editor**,
      paste this line and click **Run**:
      ```sql
      CREATE DATABASE IF NOT EXISTS switchprep;
      ```
      You should see a success message. You do not create any tables: the API creates them itself the first time
      it starts.

- [ ] **4.7 Build the database address.** In your notes file, write this line, replacing `HOST` with value 2:
      ```
      jdbc:mysql://HOST:4000/switchprep?sslMode=VERIFY_IDENTITY
      ```
      Example: `jdbc:mysql://gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/switchprep?sslMode=VERIFY_IDENTITY`

**You are done with Part 4 when:** values 2, 3 and 4 and the `jdbc:mysql://…` line are in your notes file.

---

## Part 5: start the API on Render (20 minutes, mostly waiting)

This gives you value 5, the **API address**.

Render must be allowed to read the repo, and only the repo's owner can grant that. So this part is done with
your partner's GitHub account.

- [ ] **5.1 [OWNER]** Go to <https://render.com/>, click **Get started**, and sign up **with GitHub**, using the
      account that owns the repo.

- [ ] **5.2 [OWNER] Create the service from the file in the repo.** In the Render dashboard click **New >
      Blueprint**. Connect GitHub if asked, and give Render access to the `switch_prep` repository. Select it.
      - Render reads the file `render.yaml` and shows one service named `switchprep-api`, plan **Free**. If it
        shows any price other than free, stop and ask.

- [ ] **5.3 [OWNER] Type in the five settings it asks for**, from your notes file:

      | Render asks for | Paste |
      |---|---|
      | `DB_URL` | The whole `jdbc:mysql://…` line from step 4.7 |
      | `DB_USERNAME` | Value 3 |
      | `DB_PASSWORD` | Value 4 |
      | `APP_CORS_ORIGINS` | `https://raj-alpha-swain.github.io` |
      | `APP_GOOGLE_CLIENT_ID` | Value 1 |

      No spaces before or after any value. `APP_CORS_ORIGINS` has no slash at the end.

- [ ] **5.4 [OWNER]** Click **Apply** (or **Deploy Blueprint**).

- [ ] **5.5 Wait for the first build.** Click the `switchprep-api` service to watch its log. The first build
      downloads a lot and can take 5 to 10 minutes. It is finished when the status at the top says **Live**.

- [ ] **5.6 Copy the API address** shown near the top of the service page into your notes file as value 5. It
      looks like `https://switchprep-api.onrender.com` (yours may have extra letters).

- [ ] **5.7 Test it.** In a new browser tab open value 5 followed by `/actuator/health`, for example
      `https://switchprep-api.onrender.com/actuator/health`. You should see text that starts with
      `{"status":"UP"`.

**You are done with Part 5 when:** that address shows `"status":"UP"`.

### If it does not become "Live"

Open the service's **Logs** tab and look near the bottom.

| You see | It means | Fix |
|---|---|---|
| `Production settings are incomplete: …` | One of the five settings is missing or mistyped; the message names it | Service **Environment** tab, correct the value, **Save**. It redeploys by itself |
| `Access denied for user` | Database user name or password is wrong | Recheck values 3 and 4. The user name needs the part before the dot |
| `Communications link failure` or `UnknownHostException` | The database address is wrong | Recheck the `DB_URL` line against step 4.7 |
| `Unknown database 'switchprep'` | Step 4.6 was skipped | Do step 4.6, then on Render **Manual Deploy > Deploy latest commit** |
| Anything else | | Copy the last 30 lines of the log and ask Claude |

---

## Part 6: tell the site where the API is (5 minutes)

The site is online but does not yet know the API's address or your Google client ID. You give it both, then
publish the site again.

- [ ] **6.1 [OWNER]** Repo **Settings > Secrets and variables > Actions**. Click the **Variables** tab (not
      "Secrets").

- [ ] **6.2 [OWNER]** Click **New repository variable** and create these two, one at a time:

      | Name (type exactly) | Value |
      |---|---|
      | `SWITCHPREP_API_URL` | Value 5, with no slash at the end |
      | `SWITCHPREP_GOOGLE_CLIENT_ID` | Value 1 |

      These go under Variables, not Secrets, because they are not secret: every visitor's browser receives them.

- [ ] **6.3 [OWNER] Publish the site again.** **Actions > Deploy frontend to GitHub Pages > Run workflow >
      Run workflow**, exactly as in step 2.2. Wait for the green tick.

- [ ] **6.4** Open <https://raj-alpha-swain.github.io/switch_prep/> and press **Ctrl + Shift + R** to load the
      new version. Go to **Account & Data** in the left menu.

**You are done with Part 6 when:** the Account & Data page shows a **Sign in with Google** button.

- If you still see the old text, wait two minutes and press Ctrl + Shift + R again; GitHub keeps the old file
  for a short while.

---

## Part 7: test it like a visitor (15 minutes)

Tick each row only when you see the expected result.

- [ ] **7.1 Sign in.** Click **Sign in with Google** and choose your account.
      Expect: "Signed in as *your name* (*your email*). Progress is saved to the server."
      If it says "Signing in. The sync server is waking up…", that is the sleeping API. Keep the tab open; it
      finishes within a few minutes.

- [ ] **7.2 Sync between devices.** Tick any DSA problem. Open the site on your phone, sign in with the same
      Google account. Expect: the same problem is ticked.

- [ ] **7.3 Separate accounts.** Ask your partner to sign in with their Google account on their own device.
      Expect: an empty journey. They must not see your ticks.

- [ ] **7.4 The sleeping API.** Leave the site untouched for 20 minutes. Reload and tick something.
      Expect: the top bar shows "Waking sync server…", your tick stays, and after a while the message goes away.
      **Note how long that took.** If it is regularly more than about three minutes, see Part 8.

- [ ] **7.5 Backup and restore.** On Account & Data: **Export progress** (a file downloads), then **Reset all
      progress**, then **Import progress** and choose that file. Expect: everything is back.

- [ ] **7.6 Safety check.** Open value 5 followed by `/h2-console`. Expect: an error page saying "Not Found".

- [ ] **7.7 Delete account.** With a test Google account, sign in, tick something, click **Delete my account**,
      then sign in again. Expect: an empty journey.

**If all seven are ticked, you are live.** Share <https://raj-alpha-swain.github.io/switch_prep/>.

### If sign-in fails

| What happens | Likely cause | Fix |
|---|---|---|
| Google window says "origin not allowed" or "Error 400: origin_mismatch" | Step 3.6: the origin is missing or has a slash or path | Fix it in Google **Clients**; wait 5 minutes |
| Google window says "Access blocked" or only some people can sign in | Step 3.8 not done: the app is still in "Testing" | **Audience > Publish app** |
| The Google step works, then the site says "Google sign-in failed" | Value 1 on Render is different from value 1 on GitHub | Make `APP_GOOGLE_CLIENT_ID` (Render) and `SWITCHPREP_GOOGLE_CLIENT_ID` (GitHub) identical, then redo 6.3 |
| "The server is not responding" after 5 minutes | The API is not running, or `SWITCHPREP_API_URL` is wrong | Redo step 5.7; compare the variable with value 5 |
| Signed in, but stuck on "Waking sync server…" for good | `APP_CORS_ORIGINS` on Render is not exactly `https://raj-alpha-swain.github.io` | Correct it on Render's **Environment** tab |

---

## Part 8: after you are live

**Changing the site later.** Make changes on a branch, open a pull request, merge into `main`. The site and the
API both update by themselves within a few minutes. You never repeat Parts 2 to 6.

**Things to look at in the first week**

- [ ] Render dashboard, `switchprep-api` **> Metrics**: memory should stay well under 512 MB.
- [ ] TiDB Cloud: find what backups the free plan keeps, and tell your users that **Export progress** is their
      own backup.

**Limits each account has** (to stop one person filling the free database): 5,000 tracked items, 2,000,000
characters of notes in total, 2,000 quiz attempts.

**If waking up is too slow for you**, the choices are, cheapest first:
1. Leave it. The site stays usable while it wakes.
2. Use a free "uptime monitor" website that opens the API's `/actuator/health/liveness` address every 10
   minutes, so it never sleeps. One always-on service fits inside Render's free monthly hours.
3. Move the API to Google Cloud Run, which wakes much faster but wants a payment card on file.

**Never do these**

- Never put the database password, or any value from Render's Environment tab, into the code or a chat.
- Never upload a database export to the public repo.

**Housekeeping still open**

- [ ] **[OWNER]** The old MySQL password that used to be in `application.yml` is still visible in the repo's
      history. Change that password anywhere it is really used.
- [ ] **[OWNER]** Add a LICENSE file to the repo, so others know what they may do with the code.

---

## What has already been tested, and what you are testing for the first time

Tested on the laptop before this guide was written: 25 backend tests, 11 frontend tests of the sleeping-API
behaviour, the API started in its production mode, and the built site in a real browser signed out, signed in,
and with the API switched off.

Not tested yet, because they need the real accounts you create above: signing in with a real Google account, the
API talking to TiDB Cloud, the build on Render, the real wake-up time, and the two changed GitHub workflows.
Parts 5 and 7 are where these are proven. If one fails, it is not something you did wrong: copy the message and
ask Claude.

Reference for every setting and other hosting options: [DEPLOYMENT.md](DEPLOYMENT.md).

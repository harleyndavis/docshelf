# Setting Up a Gmail Send As Alias with Squarespace Email Forwarding

This guide covers how to configure Squarespace to forward emails from a custom domain address to your Gmail inbox, then set up Gmail to send mail *as* that custom address using Google SMTP.

---

## Part 1: Set Up Email Forwarding in Squarespace

1. Log into your **Squarespace** account.
2. Click **Domains** in the left navigation.
3. Click **Email**, then click **Add Rule**.
4. Fill in the forwarding rule:
   - **Email From:** `sales@yourdomain.com`
   - **Email To:** your Gmail address (e.g., `you@gmail.com`)
5. Save the rule.

> Any email sent to `sales@yourdomain.com` will now be forwarded to your Gmail inbox.

---

## Part 2: Generate a Google App Password

> **Important:** You must generate the App Password while logged into the Gmail account that is *receiving* the forwarded emails. Using a different Gmail account will cause the sent email to appear as coming from the wrong address.

1. Go to [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
2. Make sure you're signed into the correct Gmail account.
3. Enter a name for the app (e.g., `yourdomain.com Email`).
4. Click **Create**.
5. **Copy the 16-character code** that is displayed — you'll need it shortly.

---

## Part 3: Add the Send As Alias in Gmail

1. Open **Gmail** (logged into the same account from Part 2).
2. Click the **gear icon** (Settings) in the top right, then select **See all settings**.
3. Click the **Accounts and Import** tab.
4. Under **Send mail as**, click **Add another email address**.
5. In the pop-up window, fill in:
   - **Name:** Your name or business name
   - **Email address:** `sales@yourdomain.com`
   - **Treat as alias:** ✅ Checked
6. Click **Next Step**.

---

## Part 4: Configure SMTP Settings

Fill in the SMTP settings in the next screen:

| Setting | Value |
|---|---|
| SMTP Server | `smtp.gmail.com` |
| Port | `465` |
| Username | Your Gmail address (e.g., `you@gmail.com`) |
| Password | The 16-character App Password from Part 2 |
| Connection | Secured connection using SSL |

Click **Add Account**.

---

## Part 5: Verify the Alias

1. Gmail will send a verification email to `sales@yourdomain.com`.
2. Since Squarespace forwarding is already active, this email will arrive in your Gmail inbox.
3. Click the verification link in that email to confirm that Gmail can send on behalf of `sales@yourdomain.com`.

---

You can now compose emails in Gmail and select `sales@yourdomain.com` from the **From** dropdown. Recipients will see your custom domain address as the sender.

---

## Bonus: Set Your Default Reply Behavior

Once the alias is confirmed, it's worth adjusting how Gmail handles replies:

1. Go back to **Settings → Accounts and Import**.
2. Under **Send mail as**, locate the **When replying to a message** option.
3. Set it to **Reply from the same address the message was sent to**.

This ensures that if someone emails `sales@yourdomain.com`, your reply automatically goes out from that same address rather than your personal Gmail — keeping things clean and professional without having to manually switch the From field each time.

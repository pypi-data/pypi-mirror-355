import httpx

BASE = "https://graph.microsoft.com/v1.0"
headers = lambda token: {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

def get_joined_teams(access_token):
    r = httpx.get(f"{BASE}/me/joinedTeams", headers=headers(access_token))
    r.raise_for_status()
    return r.json()["value"]

def get_channels(access_token, team_id):
    r = httpx.get(f"{BASE}/teams/{team_id}/channels", headers=headers(access_token))
    r.raise_for_status()
    return r.json()["value"]

def get_chats(access_token):
    r = httpx.get(f"{BASE}/chats", headers=headers(access_token))
    r.raise_for_status()
    return r.json()["value"]

def send_channel_message(access_token, team_id, channel_id, content):
    payload = {"body": {"content": content}}
    r = httpx.post(f"{BASE}/teams/{team_id}/channels/{channel_id}/messages",
                   headers=headers(access_token), json=payload)
    r.raise_for_status()
    return r.json()["id"]

def send_chat_message(access_token, chat_id, content):
    payload = {"body": {"content": content}}
    r = httpx.post(f"{BASE}/chats/{chat_id}/messages",
                   headers=headers(access_token), json=payload)
    r.raise_for_status()
    return r.json()["id"]

def reply_to_channel_message(access_token, team_id, channel_id, msg_id, content):
    payload = {"body": {"content": content}}
    r = httpx.post(f"{BASE}/teams/{team_id}/channels/{channel_id}/messages/"
                   f"{msg_id}/replies", headers=headers(access_token), json=payload)
    r.raise_for_status()
    return r.json()["id"]

def main():
    access_token = "eyJ0eXAiOiJKV1QiLCJub25jZSI6IjBxUGx0VC1SRTBwMzlINzVrQ0pjYjlkZld5ck5VRUNoaVpwdmpOUHFtZ00iLCJhbGciOiJSUzI1NiIsIng1dCI6IkNOdjBPSTNSd3FsSEZFVm5hb01Bc2hDSDJYRSIsImtpZCI6IkNOdjBPSTNSd3FsSEZFVm5hb01Bc2hDSDJYRSJ9.eyJhdWQiOiIwMDAwMDAwMy0wMDAwLTAwMDAtYzAwMC0wMDAwMDAwMDAwMDAiLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC84Njc3NTEwNi0wYTlmLTRhYjEtOTY0OC02MDBiMTJjYmM3YWQvIiwiaWF0IjoxNzQ5ODAwNzM2LCJuYmYiOjE3NDk4MDA3MzYsImV4cCI6MTc0OTgwNTYwMiwiYWNjdCI6MCwiYWNyIjoiMSIsImFpbyI6IkFYUUFpLzhaQUFBQWcxeGxUWFlpRWdnOWQ0SUVFWG9OUmkrTzY2UkcxbVZiOVBWb2hwd3czMXp5UXBRMXZ0UFF3R1FvRCtVTEg2S1U2Ly9WNXRtNi9tcjNyQ3hYNHlnU00wS1FOVnYzSmlXdDJ2TVAxYXFoV2pGTHlndFRMTWZJOWo3c01LSFQvZ0FKNkR1c2FKM0NxMHlPL2JFRUtCVWZYQT09IiwiYW1yIjpbInB3ZCJdLCJhcHBfZGlzcGxheW5hbWUiOiJBZ2VudFIgRGV2IiwiYXBwaWQiOiIyNjQ1ZjZkNS1kYmY0LTQ4ZDItYWQyMS1iNWEwOWVkMzBhZjMiLCJhcHBpZGFjciI6IjEiLCJmYW1pbHlfbmFtZSI6IlJhbmphbiIsImdpdmVuX25hbWUiOiJBbmtpdCIsImlkdHlwIjoidXNlciIsImlwYWRkciI6IjExNy4yNTAuMTYxLjIyMiIsIm5hbWUiOiJBbmtpdCBSYW5qYW4iLCJvaWQiOiJlMmJlZWMyYy1mNTViLTQ2OTEtOGJjNi0yOGRmZmQyMWEwOGMiLCJwbGF0ZiI6IjUiLCJwdWlkIjoiMTAwMzIwMDQ3QkI2M0NGMiIsInJoIjoiMS5BYjRBQmxGM2hwOEtzVXFXU0dBTEVzdkhyUU1BQUFBQUFBQUF3QUFBQUFBQUFBQjdBZDItQUEuIiwic2NwIjoiQ2hhbm5lbC5SZWFkQmFzaWMuQWxsIENoYW5uZWxNZXNzYWdlLkVkaXQgQ2hhbm5lbE1lc3NhZ2UuU2VuZCBDaGF0LkNyZWF0ZSBDaGF0LlJlYWQgQ2hhdC5SZWFkQmFzaWMgQ2hhdC5SZWFkV3JpdGUgQ2hhdE1lc3NhZ2UuUmVhZCBDaGF0TWVzc2FnZS5TZW5kIEZpbGVzLlJlYWQuQWxsIEZpbGVzLlJlYWRXcml0ZS5BbGwgRmlsZXMuUmVhZFdyaXRlLkFwcEZvbGRlciBNYWlsLlJlYWQgTWFpbC5SZWFkV3JpdGUgTWFpbC5TZW5kIFNpdGVzLkZ1bGxDb250cm9sLkFsbCBTaXRlcy5SZWFkV3JpdGUuQWxsIFRlYW0uQ3JlYXRlIFRlYW0uUmVhZEJhc2ljLkFsbCBUZWFtc0FjdGl2aXR5LlJlYWQgVGVhbXNBY3Rpdml0eS5TZW5kIFRlYW1zVGFiLlJlYWRXcml0ZUZvclVzZXIgVGVhbXNUYWIuUmVhZFdyaXRlU2VsZkZvclVzZXIgVXNlci5SZWFkIHByb2ZpbGUgb3BlbmlkIGVtYWlsIiwic2lkIjoiMDA1YmUzODktMGFkZC02ZmJkLTE5ODYtZGUyZGRlNGNkZjhiIiwic2lnbmluX3N0YXRlIjpbImttc2kiXSwic3ViIjoidk41a2FzYzVtWUp2VTJheXg3LW1EaF9QSHkxUDk2Y0xnWFhuMTcycjZwayIsInRlbmFudF9yZWdpb25fc2NvcGUiOiJBUyIsInRpZCI6Ijg2Nzc1MTA2LTBhOWYtNGFiMS05NjQ4LTYwMGIxMmNiYzdhZCIsInVuaXF1ZV9uYW1lIjoiYW5raXRAYWdlbnRyLmRldiIsInVwbiI6ImFua2l0QGFnZW50ci5kZXYiLCJ1dGkiOiJjRG1tbndhV3kwQ3JFSGZ4bjNjSkFBIiwidmVyIjoiMS4wIiwid2lkcyI6WyJiNzlmYmY0ZC0zZWY5LTQ2ODktODE0My03NmIxOTRlODU1MDkiXSwieG1zX2Z0ZCI6Imdqb3h3REdqS2Jrd0NMRC1vak5TYnd1Vk5hUW43NGlaMnhaV1Fsam9sUUVCWVhOcFlYTnZkWFJvWldGemRDMWtjMjF6IiwieG1zX2lkcmVsIjoiMSAzMCIsInhtc19zdCI6eyJzdWIiOiI0Y0xWREg1VGxiVUp6N2poRTZHeEhjUjBSdTd6Z3B6TUU1YlRTTzFGVzBnIn0sInhtc190Y2R0IjoxNzQzODY1Mjc5fQ.OsVVy_hAAxYPJoA2HW2Hb7I8XQlwVBL_Sd6XoLQS_7nneYzV-hL37O-H70NCbXlAFqORfern8HbgN5qJyI5AU-t-89KVenySGw_w8eM_hOKGOkLNcPrWlO2N_zx41z2LQkMPAaKpJuUT5fBWo2av9INOVYITBf_Lt0qIha4SFKPUuIDvzHy1f9aTFF-tgbVjppPKnB_pMX7ZWtRyywpII0l1fVLb8t0IIpK6Tbc7GhL96-rp71PpysQm2FINQXo8YoYUldieW_tvfQyRwRuD8-aO828URnT3T47nAs1wllAMneizk5IKrsMu4s0CRcXOEH6CBVjfJHYRGoadNz_BGA"
    # 1. Get teams → team-id
    # teams = get_joined_teams(access_token)
    # team_id = teams[0]["id"]
    # print("team-id:", team_id)

    # 2. Get channels → channel-id
    # channels = get_channels(access_token, team_id)
    # channel_id = channels[0]["id"]
    # print("channel-id:", channel_id)

    # 3. Send message → message-id
    # msg_id = send_channel_message(access_token, team_id, channel_id, "Hello Channel!")
    # print("message‑id:", msg_id)

    # 4. Reply → reply-id
    # reply_id = reply_to_channel_message(access_token, team_id, channel_id, msg_id, "A reply")
    # print("reply‑id:", reply_id)

    # 5. Get chats → chat-id
    chats = get_chats(access_token)
    chat_id = chats[0]["id"]
    print("chat‑id:", chat_id)

    # 6. Send chat message → message-id
    # chat_msg_id = send_chat_message(access_token, chat_id, "Hello Chat!")
    # print("chatMessage‑id:", chat_msg_id)

if __name__ == "__main__":
    main()

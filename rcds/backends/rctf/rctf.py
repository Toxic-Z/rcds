from base64 import b64encode
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urljoin

import requests
from requests_toolbelt.sessions import BaseUrlSession  # type: ignore


class RCTFAdminV1:

    session: requests.Session

    def __init__(self, endpoint: str, login_token: Optional[str]):
        print(f"--- setting up rctfadminv1 object")
        print(f"--- endpoint: {endpoint}")
        #print(f"--- login_token: {b64encode(login_token.encode()).decode() if login_token is not None else '<none>'}")

        self.session = BaseUrlSession(urljoin(endpoint, "api/v1/admin/"))

        if login_token is not None:
            login_resp = requests.post(
                urljoin(endpoint, "api/v1/auth/login"), json={"teamToken": login_token}
            ).json()
            if login_resp["kind"] == "goodLogin":
                auth_token = login_resp["data"]["authToken"]
                self.session.headers["Authorization"] = f"Bearer {auth_token}"
            else:
                raise ValueError(
                    f"Invalid login_token provided (reason: {login_resp['kind']})"
                )

    @staticmethod
    def assertResponseKind(response: Any, kind: str) -> None:
        if response["kind"] != kind:
            raise RuntimeError(f"Server error: {response['kind']}")

    def list_challenges(self) -> List[Dict[str, Any]]:
        r = self.session.get("challs").json()
        self.assertResponseKind(r, "goodChallenges")
        return r["data"]

    def put_challenge(self, chall_id: str, data: Dict[str, Any]) -> None:
        r = self.session.put("challs/" + quote(chall_id), json={"data": data}).json()
        self.assertResponseKind(r, "goodChallengeUpdate")

    def delete_challenge(self, chall_id: str) -> None:
        r = self.session.delete("challs/" + quote(chall_id)).json()
        self.assertResponseKind(r, "goodChallengeDelete")

    def create_upload(self, uploads: Dict[str, bytes]) -> Dict[str, str]:
        """
        :param uploads: uploads {name: data}
        :return: urls {name: url}
        """
        if len(uploads) == 0:
            return {}
        payload = [
            {"name": name, "data": "data:;base64," + b64encode(data).decode()}
            for name, data in uploads.items()
        ]
        r = self.session.post("upload", json={"files": payload}).json()
        self.assertResponseKind(r, "goodFilesUpload")
        return {f["name"]: f["url"] for f in r["data"]}

    def get_url_for_files(self, files: Dict[str, str]) -> Dict[str, Optional[str]]:
        """
        :param files: files to get {name: sha256}
        :return: urls {name: url}
        """
        payload = [{"name": name, "sha256": sha256} for name, sha256 in files.items()]
        r = self.session.post("upload/query", json={"uploads": payload}).json()
        self.assertResponseKind(r, "goodUploadsQuery")
        return {f["name"]: f["url"] for f in r["data"]}

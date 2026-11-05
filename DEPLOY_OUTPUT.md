[2026-11-05T12:21:56.184Z] ----------------------------------------------------------------------
[2026-11-05T12:21:56.187Z] Command:       /opt/hostedtoolcache/node/20.20.2/x64/bin/node /home/runner/.npm/_npx/7750544ccf494d8b/node_modules/.bin/firebase deploy --only hosting --project volt-rs --debug --non-interactive
[2026-11-05T12:21:56.187Z] CLI Version:   15.35.0
[2026-11-05T12:21:56.188Z] Platform:      linux
[2026-11-05T12:21:56.188Z] Node Version:  v20.20.2
[2026-11-05T12:21:56.188Z] Detected Agent: unknown
[2026-11-05T12:21:56.188Z] Time:          Thu Nov 05 2026 12:21:56 GMT+0000 (Coordinated Universal Time)
[2026-11-05T12:21:56.188Z] ----------------------------------------------------------------------

[2026-11-05T12:21:56.985Z] > command requires scopes: ["email","openid","https://www.googleapis.com/auth/cloudplatformprojects.readonly","https://www.googleapis.com/auth/firebase","https://www.googleapis.com/auth/cloud-platform"]
[2026-11-05T12:21:57.098Z] Running auto auth
[2026-11-05T12:21:57.099Z] [iam] checking project volt-rs for permissions ["firebase.projects.get","firebasehosting.sites.update"]
[2026-11-05T12:21:57.100Z] No OAuth tokens found
[2026-11-05T12:21:57.101Z] >>> [apiv2][query] POST https://cloudresourcemanager.googleapis.com/v1/projects/volt-rs:testIamPermissions [none]
[2026-11-05T12:21:57.102Z] >>> [apiv2][(partial)header] POST https://cloudresourcemanager.googleapis.com/v1/projects/volt-rs:testIamPermissions  x-goog-user-project=volt-rs
[2026-11-05T12:21:57.102Z] >>> [apiv2][body] POST https://cloudresourcemanager.googleapis.com/v1/projects/volt-rs:testIamPermissions {"permissions":["firebase.projects.get","firebasehosting.sites.update"]}
[2026-11-05T12:21:57.212Z] <<< [apiv2][status] POST https://cloudresourcemanager.googleapis.com/v1/projects/volt-rs:testIamPermissions 200
[2026-11-05T12:21:57.212Z] <<< [apiv2][body] POST https://cloudresourcemanager.googleapis.com/v1/projects/volt-rs:testIamPermissions {"permissions":["firebase.projects.get","firebasehosting.sites.update"]}
[2026-11-05T12:21:57.213Z] No OAuth tokens found
[2026-11-05T12:21:57.213Z] >>> [apiv2][query] GET https://serviceusage.googleapis.com/v1/projects/volt-rs/services/firebasehosting.googleapis.com [none]
[2026-11-05T12:21:57.213Z] >>> [apiv2][(partial)header] GET https://serviceusage.googleapis.com/v1/projects/volt-rs/services/firebasehosting.googleapis.com  x-goog-user-project=volt-rs
[2026-11-05T12:21:57.639Z] <<< [apiv2][status] GET https://serviceusage.googleapis.com/v1/projects/volt-rs/services/firebasehosting.googleapis.com 403
[2026-11-05T12:21:57.639Z] <<< [apiv2][body] GET https://serviceusage.googleapis.com/v1/projects/volt-rs/services/firebasehosting.googleapis.com [omitted]

Error: Request to https://serviceusage.googleapis.com/v1/projects/volt-rs/services/firebasehosting.googleapis.com had HTTP Error: 403, Permission denied to get service [firebasehosting.googleapis.com]
Help Token: AaVM3aMxkn_GA_7m0xevtbjIpMR-rBB5taO77Hwamz-g9N2b-tXizPxKtx0hitXB9Nu2ZYDWkTDj9lgpnY_dZq1sWGLs72H7H61V4U25fhpYf_vf
[2026-11-05T12:21:57.640Z] Error Context: {
  "body": {
    "error": {
      "code": 403,
      "message": "Permission denied to get service [firebasehosting.googleapis.com]\nHelp Token: AaVM3aMxkn_GA_7m0xevtbjIpMR-rBB5taO77Hwamz-g9N2b-tXizPxKtx0hitXB9Nu2ZYDWkTDj9lgpnY_dZq1sWGLs72H7H61V4U25fhpYf_vf",
      "status": "PERMISSION_DENIED",
      "details": [
        {
          "@type": "type.googleapis.com/google.rpc.PreconditionFailure",
          "violations": [
            {
              "type": "googleapis.com",
              "subject": "?error_code=110002&service=serviceusage.googleapis.com&permission=serviceusage.services.get&error_info_id=CiQwMWExYWJhOC1hMGVkLTczM2ItODI0Zi0xNjY0Njc3NTk1ZTYSPXByb2plY3RzLzUzNzg5MzE0MDQ2OC9zZXJ2aWNlcy9maXJlYmFzZWhvc3RpbmcuZ29vZ2xlYXBpcy5jb20%3D&troubleshooter_url=https://console.cloud.google.com/iam-admin/troubleshooter/summary;errorId%3DCiQwMWExYWJhOC1hMGVkLTczM2ItODI0Zi0xNjY0Njc3NTk1ZTYSPXByb2plY3RzLzUzNzg5MzE0MDQ2OC9zZXJ2aWNlcy9maXJlYmFzZWhvc3RpbmcuZ29vZ2xlYXBpcy5jb20%253D"
            }
          ]
        },
        {
          "@type": "type.googleapis.com/google.rpc.ErrorInfo",
          "reason": "AUTH_PERMISSION_DENIED",
          "domain": "serviceusage.googleapis.com",
          "metadata": {
            "service": "serviceusage.googleapis.com",
            "permission": "serviceusage.services.get",
            "error_info_id": "CiQwMWExYWJhOC1hMGVkLTczM2ItODI0Zi0xNjY0Njc3NTk1ZTYSPXByb2plY3RzLzUzNzg5MzE0MDQ2OC9zZXJ2aWNlcy9maXJlYmFzZWhvc3RpbmcuZ29vZ2xlYXBpcy5jb20=",
            "troubleshooter_url": "https://console.cloud.google.com/iam-admin/troubleshooter/summary;errorId=CiQwMWExYWJhOC1hMGVkLTczM2ItODI0Zi0xNjY0Njc3NTk1ZTYSPXByb2plY3RzLzUzNzg5MzE0MDQ2OC9zZXJ2aWNlcy9maXJlYmFzZWhvc3RpbmcuZ29vZ2xlYXBpcy5jb20%3D"
          }
        }
      ]
    }
  },
  "response": {
    "statusCode": 403
  }
}

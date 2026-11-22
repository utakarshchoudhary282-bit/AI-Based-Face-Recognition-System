# Identity Verification Procedure (Face Verification)

Company: Orion Nexus Technologies Pvt. Ltd. (fictional) | Policy owner: Corporate Security | Version 1.4

## 1. When verification is required
Security staff must verify identity at the main entrance, before granting entry to any L3 or L4 zone, when an employee has forgotten their ID card, and whenever a person's identity is in doubt.

## 2. Using the Employee Verification Portal
1. Log in with your own portal user ID and password. Never share your login.
2. Capture a clear, front-facing photo with the webcam, or upload a photo taken at the desk.
3. The portal detects the face and the AI model returns the most likely employee and a face similarity score between 0 and 1.
4. Check the result card: name, employee code, department, access level and status.

## 3. Confidence rules
- **Similarity 0.45 or higher - Match:** the person may be treated as verified, if the employee's status is Active and their access level allows the requested zone.
- **Similarity below 0.45 - Unknown:** do not grant entry based on the photo. Ask for the physical ID card and a government photo ID, and call the reporting manager to confirm.
- **No face detected:** retake the photo with better lighting, the person facing the camera, and no mask, cap or sunglasses.
- If two attempts in a row give "Unknown", stop retrying and follow the manual check in section 4.

## 4. Manual check (fallback)
Match the physical ID card photo to the person, confirm the employee code with HR or the reporting manager by phone, and record the manual check in the visitor and exception register. The AI result alone is never enough to override a mismatch noticed by the security officer.

## 5. Status warnings
If the verified employee's status is Suspended or Exited, deny entry, do not argue, and inform HR and the Security Supervisor immediately. If the status is On Leave, allow entry only with HR or manager approval (see Access Control Policy).

## 6. Logging
Every verification attempt is logged automatically with the portal user, time, predicted employee, similarity score and result (MATCH, UNKNOWN or NO_FACE). Logs are kept for 90 days and can be viewed only by admins.

## 7. Model updates
When a new employee joins, an admin uploads at least 10 clear face photos (different angles and lighting) and retrains the model. When an employee exits, their photos are deleted and the model is retrained within 30 days.

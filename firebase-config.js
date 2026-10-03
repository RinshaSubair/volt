/**
 * Volt EEE Platform - Firebase Configuration & Cloud Sync Module
 * ==============================================================
 * This module configures Firebase Authentication and Cloud Firestore
 * for the exclusive 60-student batch cohort.
 *
 * Self-registration is strictly disabled across the platform.
 * Authorized student accounts are provisioned via `tools/create_volt_user.py`.
 */

const voltFirebaseConfig = {
  apiKey: "AIzaSyAuQJeEePogtOzcKQGLi2yR_N1WrHdv8To",
  authDomain: "volt-rs.firebaseapp.com",
  projectId: "volt-rs",
  storageBucket: "volt-rs.firebasestorage.app",
  messagingSenderId: "537893140468",
  appId: "1:537893140468:web:a9c5c358952393acacaba1",
  measurementId: "G-EB3X006BL6"
};

// Export configuration for browser or Node environments
if (typeof module !== "undefined" && module.exports) {
  module.exports = { voltFirebaseConfig };
}

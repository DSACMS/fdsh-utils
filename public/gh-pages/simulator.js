const { createApp, ref, computed } = Vue;

createApp({
  setup() {
    const educationRequestInput = ref(JSON.stringify({
      "educationRequest": {
        "personGivenName": "Lillie",
        "personSurName": "Venson",
        "consent": {
          "status": "not_provided",
          "assertedAt": new Date().toISOString(),
          "scope": ["enrollment_verification"]
        },
        "termsAcceptedIndicator": true,
        "personSocialSecurityNumber": "999887777",
        "personBirthDate": "2001-09-23"
      }
    }, null, 2));

    const inNscDatabase = ref(true);
    const inNsldsDatabase = ref(true);

    const simulationResult = ref(null);
    const sourcesChecked = ref([]);
    const sourcesNotChecked = ref([]);
    const error = ref(null);

    const loadExample = (type) => {
      let payload = {};
      const assertedAt = new Date().toISOString();
      const scope = ["enrollment_verification"];

      if (type === 'identity') {
        payload = {
          "educationRequest": {
            "personGivenName": "Lillie",
            "personSurName": "Venson",
            "consent": {
              "status": "not_provided",
              "assertedAt": assertedAt,
              "scope": scope
            },
            "termsAcceptedIndicator": true,
            "personBirthDate": "2001-09-23"
          }
        };
      } else if (type === 'ssnOnly') {
        payload = {
          "educationRequest": {
            "personSocialSecurityNumber": "999887777",
            "consent": {
              "status": "not_provided",
              "assertedAt": assertedAt,
              "scope": scope
            },
            "termsAcceptedIndicator": true
          }
        };
      } else if (type === 'ssnIdentity') {
        payload = {
          "educationRequest": {
            "personGivenName": "Lillie",
            "personSurName": "Venson",
            "personSocialSecurityNumber": "999887777",
            "consent": {
              "status": "not_provided",
              "assertedAt": assertedAt,
              "scope": scope
            },
            "termsAcceptedIndicator": true,
            "personBirthDate": "2001-09-23"
          }
        };
      } else if (type === 'identityConsent') {
        payload = {
          "educationRequest": {
            "personGivenName": "Lillie",
            "personSurName": "Venson",
            "consent": {
              "status": "granted",
              "assertedAt": assertedAt,
              "scope": scope
            },
            "termsAcceptedIndicator": true,
            "personBirthDate": "2001-09-23"
          }
        };
      } else if (type === 'ssnOnlyConsent') {
        payload = {
          "educationRequest": {
            "personSocialSecurityNumber": "999887777",
            "consent": {
              "status": "granted",
              "assertedAt": assertedAt,
              "scope": scope
            },
            "termsAcceptedIndicator": true
          }
        };
      } else if (type === 'ssnIdentityConsent') {
        payload = {
          "educationRequest": {
            "personGivenName": "Lillie",
            "personSurName": "Venson",
            "personSocialSecurityNumber": "999887777",
            "consent": {
              "status": "granted",
              "assertedAt": assertedAt,
              "scope": scope
            },
            "termsAcceptedIndicator": true,
            "personBirthDate": "2001-09-23"
          }
        };
      }
      educationRequestInput.value = JSON.stringify(payload, null, 2);
    };

    const simulate = () => {
      error.value = null;
      simulationResult.value = null;
      sourcesChecked.value = [];
      sourcesNotChecked.value = [];

      let requestData;
      try {
        requestData = JSON.parse(educationRequestInput.value);
      } catch (e) {
        error.value = "Invalid JSON input: " + e.message;
        return;
      }

      const educationRequest = requestData.educationRequest;
      if (!educationRequest) {
        error.value = "Missing 'educationRequest' object in payload.";
        return;
      }

      // Check for consent and termsAcceptedIndicator as per the prompt's example
      if (educationRequest.termsAcceptedIndicator !== true) {
        error.value = "termsAcceptedIndicator must be true to proceed.";
        return;
      }

      const hasSsn = !!educationRequest.personSocialSecurityNumber;
      const hasIdentityInfo = !!(educationRequest.personGivenName && educationRequest.personBirthDate);
      const isSsnOnly = hasSsn && !hasIdentityInfo;
      const isConsentGranted = educationRequest.consent?.status === 'granted';

      let hitNsc = false;
      let hitNslds = false;

      // 1. Evaluate NSLDS (Prioritized)
      if (hasSsn) {
        sourcesChecked.value.push("NSLDS (via SSN)");
        hitNslds = inNsldsDatabase.value;
      } else {
        sourcesNotChecked.value.push("NSLDS (Bypassed: No SSN provided)");
      }

      // Short-circuit if NSLDS match is found
      if (hitNslds) {
        sourcesNotChecked.value.push("NSC (Short-circuited: NSLDS match found)");
        simulationResult.value = generateResponse(true, hasSsn, educationRequest, "NSLDS");
        return;
      }

      // 2. Evaluate NSC
      if (hasIdentityInfo) {
        if (isSsnOnly && !isConsentGranted) {
          sourcesNotChecked.value.push("NSC (Blocked: SSN-only requires consent status 'granted')");
        } else {
          const label = hasSsn ? "NSC (Identity-based Fallback)" : "NSC (Identity-based)";
          sourcesChecked.value.push(label);
          hitNsc = inNscDatabase.value;
        }
      } else {
        if (isSsnOnly && isConsentGranted) {
          const label = hasSsn ? "NSC (Identity-based Fallback)" : "NSC (Identity-based)";
          sourcesChecked.value.push(label);
          hitNsc = inNscDatabase.value;
        } else {
          sourcesNotChecked.value.push("NSC (Bypassed: Missing Names/DOB, SSN-only requires consent status 'granted')");
        }
      }

      const hit = hitNsc || hitNslds;

      // Determine final source for attribution (important for transaction fees)
      let finalSource = "None";
      if (hitNslds) {
        finalSource = "NSLDS";
      } else if (hasIdentityInfo && !(isSsnOnly && !isConsentGranted)) {
        // If we attempted to hit NSC (not blocked or bypassed), attribute it to NSC
        finalSource = "National Student Clearinghouse";
      }

      simulationResult.value = generateResponse(hit, hasSsn, educationRequest, finalSource);
    };

    const generateResponse = (hit, hasSsn, educationRequest, sourceName) => {
      const response = {
        "educationResponse": {
          "enrollmentFound": hit,
          "dataSource": sourceName
        }
      };

      // Only include nscTransactionDetails for NSC source (NSLDS/Dept of Ed doesn't have this)
      if (sourceName === "National Student Clearinghouse") {
        response.educationResponse.nscTransactionDetails = {
          "transactionId": "SIM-" + Math.random().toString(36).substr(2, 9).toUpperCase(),
          "orderId": "ORD-" + Math.random().toString(36).substr(2, 9).toUpperCase(),
          "transactionStatusCode": "CNF",
          "transactionFee": "1.00",
          "salesTax": "0.03",
          "transactionTotal": "1.03",
          "requestedByText": "SIMULATOR",
          "requestedDateTimeText": new Date().toISOString().replace('T', ' ').substr(0, 23)
        };
      }

      if (hit) {
        if (!hasSsn) {
           response.educationResponse.studentInfoProvided = {
             "personSurName": educationRequest.personSurName,
             "personGivenName": educationRequest.personGivenName,
             "personBirthDate": educationRequest.personBirthDate
           };
        }

        response.educationResponse.enrollmentDetails = [
          {
            "officialSchoolName": "SIMULATED UNIVERSITY",
            "schoolCode": "123456",
            "enrollmentData": [
              {
                "enrollmentStatusCode": "F",
                "termBeginDate": "2022-09-01",
                "termEndDate": "2023-05-30",
                "schoolCertifiedOnDate": "2023-06-01"
              }
            ]
          }
        ];
      }
      return response;
    };

    return {
      educationRequestInput,
      inNscDatabase,
      inNsldsDatabase,
      simulationResult,
      sourcesChecked,
      sourcesNotChecked,
      error,
      loadExample,
      simulate
    };
  }
}).mount('#app');

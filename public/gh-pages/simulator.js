const { createApp, ref, computed } = Vue;

createApp({
  setup() {
    const nscRequestInput = ref(JSON.stringify({
      "nscRequest": {
        "personGivenName": "Lillie",
        "personSurName": "Venson",
        "consent": false,
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
      if (type === 'identity') {
        payload = {
          "nscRequest": {
            "personGivenName": "Lillie",
            "personSurName": "Venson",
            "consent": false,
            "termsAcceptedIndicator": true,
            "personBirthDate": "2001-09-23"
          }
        };
      } else if (type === 'ssnOnly') {
        payload = {
          "nscRequest": {
            "personSocialSecurityNumber": "999887777",
            "consent": false,
            "termsAcceptedIndicator": true
          }
        };
      } else if (type === 'ssnIdentity') {
        payload = {
          "nscRequest": {
            "personGivenName": "Lillie",
            "personSurName": "Venson",
            "personSocialSecurityNumber": "999887777",
            "consent": false,
            "termsAcceptedIndicator": true,
            "personBirthDate": "2001-09-23"
          }
        };
      } else if (type === 'identityConsent') {
        payload = {
          "nscRequest": {
            "personGivenName": "Lillie",
            "personSurName": "Venson",
            "consent": true,
            "termsAcceptedIndicator": true,
            "personBirthDate": "2001-09-23"
          }
        };
      } else if (type === 'ssnOnlyConsent') {
        payload = {
          "nscRequest": {
            "personSocialSecurityNumber": "999887777",
            "consent": true,
            "termsAcceptedIndicator": true
          }
        };
      } else if (type === 'ssnIdentityConsent') {
        payload = {
          "nscRequest": {
            "personGivenName": "Lillie",
            "personSurName": "Venson",
            "personSocialSecurityNumber": "999887777",
            "consent": true,
            "termsAcceptedIndicator": true,
            "personBirthDate": "2001-09-23"
          }
        };
      }
      nscRequestInput.value = JSON.stringify(payload, null, 2);
    };

    const simulate = () => {
      error.value = null;
      simulationResult.value = null;
      sourcesChecked.value = [];
      sourcesNotChecked.value = [];

      let requestData;
      try {
        requestData = JSON.parse(nscRequestInput.value);
      } catch (e) {
        error.value = "Invalid JSON input: " + e.message;
        return;
      }

      const nscRequest = requestData.nscRequest;
      if (!nscRequest) {
        error.value = "Missing 'nscRequest' object in payload.";
        return;
      }

      // Check for consent and termsAcceptedIndicator as per the prompt's example
      // Update: If consent is false, we can still proceed but cannot use SSN-based sources
      if (nscRequest.termsAcceptedIndicator !== true) {
        error.value = "termsAcceptedIndicator must be true to proceed.";
        return;
      }

      const hasSsn = !!nscRequest.personSocialSecurityNumber;
      const hasIdentityInfo = !!(nscRequest.personGivenName && nscRequest.personBirthDate);
      const isSsnOnly = hasSsn && !hasIdentityInfo;

      let hitNsc = false;
      let hitNslds = false;

      // 1. Evaluate NSLDS (Prioritized)
      if (hasSsn) {
        if (nscRequest.consent !== false) {
          sourcesChecked.value.push("NSLDS (via SSN)");
          hitNslds = inNsldsDatabase.value;
        } else {
          sourcesNotChecked.value.push("NSLDS (Blocked: SSN requires consent)");
        }
      } else {
        sourcesNotChecked.value.push("NSLDS (Bypassed: No SSN provided)");
      }

      // Short-circuit if NSLDS match is found
      if (hitNslds) {
        sourcesNotChecked.value.push("NSC (Short-circuited: NSLDS match found)");
        simulationResult.value = generateResponse(true, hasSsn, nscRequest, "NSLDS");
        return;
      }

      // 2. Evaluate NSC
      if (hasIdentityInfo) {
        if (isSsnOnly && nscRequest.consent === false) {
          sourcesNotChecked.value.push("NSC (Blocked: SSN-only requires consent)");
        } else {
          const label = hasSsn ? "NSC (Identity-based Fallback)" : "NSC (Identity-based)";
          sourcesChecked.value.push(label);
          hitNsc = inNscDatabase.value;
        }
      } else {
        sourcesNotChecked.value.push("NSC (Bypassed: Missing Names/DOB)");
      }

      const hit = hitNsc || hitNslds;

      // Determine final source for attribution (important for transaction fees)
      let finalSource = "None";
      if (hitNslds) {
        finalSource = "NSLDS";
      } else if (hasIdentityInfo && !(isSsnOnly && nscRequest.consent === false)) {
        // If we attempted to hit NSC (not blocked or bypassed), attribute it to NSC
        finalSource = "National Student Clearinghouse";
      }

      simulationResult.value = generateResponse(hit, hasSsn, nscRequest, finalSource);
    };

    const generateResponse = (hit, hasSsn, nscRequest, sourceName) => {
      const response = {
        "nscResponse": {
          "enrollmentFound": hit,
          "dataSource": sourceName
        }
      };

      // Only include nscTransactionDetails for NSC source (NSLDS/Dept of Ed doesn't have this)
      if (sourceName === "National Student Clearinghouse") {
        response.nscResponse.nscTransactionDetails = {
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
           response.nscResponse.studentInfoProvided = {
             "personSurName": nscRequest.personSurName,
             "personGivenName": nscRequest.personGivenName,
             "personBirthDate": nscRequest.personBirthDate
           };
        }

        response.nscResponse.enrollmentDetails = [
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
      nscRequestInput,
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

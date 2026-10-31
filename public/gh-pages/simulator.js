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
      }
      nscRequestInput.value = JSON.stringify(payload, null, 2);
    };

    const simulate = () => {
      error.value = null;
      simulationResult.value = null;
      sourcesChecked.value = [];

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

      if (hasSsn && nscRequest.consent !== false) {
        // Prioritize NSLDS if SSN is available and consent is given
        sourcesChecked.value.push("NSLDS (via SSN)");
        hitNslds = inNsldsDatabase.value;

        if (hitNslds) {
          // If found in NSLDS, we are done
          simulationResult.value = generateResponse(true, hasSsn, nscRequest);
          return;
        }

        // If not found in NSLDS and we have identity info, try NSC
        if (hasIdentityInfo) {
          sourcesChecked.value.push("NSC (Identity-based Fallback)");
          hitNsc = inNscDatabase.value;
        }
      } else if (nscRequest.consent === false) {

       if(hasSsn) {
         sourcesChecked.value.push("NSLDS (via SSN)");
         hitNslds = inNsldsDatabase.value;

         if (hitNslds) {
           // If found in NSLDS, we are done
           simulationResult.value = generateResponse(true, hasSsn, nscRequest);
           return;
         }
       }
       if(isSsnOnly) {
         sourcesChecked.value.push("Blocked: NSC (SSN-only requires consent)");
       }
        // If not found in NSLDS and we have identity info, try NSC
        if (hasIdentityInfo) {
          sourcesChecked.value.push("NSC (Identity-based Fallback)");
          hitNsc = inNscDatabase.value;
        }
      }

      const hit = hitNsc || hitNslds;

      simulationResult.value = generateResponse(hit, hasSsn, nscRequest);
    };

    const generateResponse = (hit, hasSsn, nscRequest) => {
      const response = {
        "nscResponse": {
          "transactionDetails": {
            "transactionId": "SIM-" + Math.random().toString(36).substr(2, 9).toUpperCase(),
            "orderId": "ORD-" + Math.random().toString(36).substr(2, 9).toUpperCase(),
            "transactionStatusCode": "CNF",
            "transactionFee": "0.00",
            "salesTax": "0.00",
            "transactionTotal": "0.00",
            "requestedByText": "SIMULATOR",
            "requestedDateTimeText": new Date().toISOString().replace('T', ' ').substr(0, 23),
            "nscHitIndicator": hit
          }
        }
      };

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
      error,
      loadExample,
      simulate
    };
  }
}).mount('#app');

const { createApp, ref, computed, onMounted } = Vue;

createApp({
  setup() {
    const allExperiments = ref([]);
    const activeSource = ref("All");
    const searchQuery = ref("");
    const selectedSchema = ref(null);
    const selectedSchemaName = ref("");
    const selectedSchemaProtocol = ref("");

    const dataSources = computed(() => {
      const sources = allExperiments.value.map(
        (exp) => exp.data_sources || "Unknown",
      );
      return [...new Set(sources)].sort();
    });

    const filteredExperiments = computed(() => {
      let filtered = allExperiments.value;

      if (activeSource.value !== "All") {
        filtered = filtered.filter(
          (exp) => (exp.data_sources || "Unknown") === activeSource.value,
        );
      }

      if (searchQuery.value.trim() !== "") {
        const query = searchQuery.value.toLowerCase();
        filtered = filtered.filter(
          (exp) =>
            exp.service_name.toLowerCase().includes(query) ||
            exp.primary_purpose.toLowerCase().includes(query) ||
            (exp.protocol && exp.protocol.toLowerCase().includes(query)) ||
            (exp.notes && exp.notes.toLowerCase().includes(query)) ||
            (exp.document_links &&
              exp.document_links.some((doc) =>
                doc.name.toLowerCase().includes(query),
              )),
        );
      }

      return filtered;
    });

    const filteredGroupedExperiments = computed(() => {
      const grouped = {};
      filteredExperiments.value.forEach((exp) => {
        const source = exp.data_sources || "Unknown";
        if (!grouped[source]) {
          grouped[source] = [];
        }
        grouped[source].push(exp);
      });

      // Sort keys
      return Object.keys(grouped)
        .sort()
        .reduce((obj, key) => {
          obj[key] = grouped[key];
          return obj;
        }, {});
    });

    onMounted(async () => {
      try {
        const response = await fetch("data.json");
        allExperiments.value = await response.json();
      } catch (error) {
        console.error("Error loading data:", error);
      }
    });

    const showFutureFeatureAlert = () => {
      alert(
        "This will be added as a feature in a future release, reach out and flag an issue if you want this faster!",
      );
    };

    const showSchema = (exp) => {
      selectedSchema.value = exp.response_schema;
      selectedSchemaName.value = exp.service_name;
      selectedSchemaProtocol.value = exp.protocol;
    };

    const parsedSchemaElements = computed(() => {
      if (!selectedSchema.value) return null;

      // Check for XML
      if (
        typeof selectedSchema.value === "string" &&
        selectedSchema.value.trim().startsWith("<?xml")
      ) {
        try {
          const parser = new DOMParser();
          const xmlDoc = parser.parseFromString(
            selectedSchema.value,
            "text/xml",
          );
          const elements = [];

          const xsdElements = xmlDoc.getElementsByTagNameNS(
            "http://www.w3.org/2001/XMLSchema",
            "element",
          );
          for (let i = 0; i < xsdElements.length; i++) {
            const el = xsdElements[i];
            const name = el.getAttribute("name");
            const type = el.getAttribute("type");
            if (name) {
              elements.push({
                name,
                type: type || "anonymous",
                kind: "Element",
              });
            }
          }

          const xsdComplexTypes = xmlDoc.getElementsByTagNameNS(
            "http://www.w3.org/2001/XMLSchema",
            "complexType",
          );
          for (let i = 0; i < xsdComplexTypes.length; i++) {
            const ct = xsdComplexTypes[i];
            const name = ct.getAttribute("name");
            if (name) {
              elements.push({
                name,
                type: "ComplexType",
                kind: "Type Definition",
              });
            }
          }
          return elements.length > 0 ? elements : null;
        } catch (e) {
          console.error("Error parsing XML schema:", e);
          return null;
        }
      }

      // Check for JSON Schema
      if (
        typeof selectedSchema.value === "object" &&
        selectedSchema.value !== null
      ) {
        try {
          const elements = [];
          const props = selectedSchema.value.properties;

          if (props) {
            Object.keys(props).forEach((key) => {
              const prop = props[key];
              elements.push({
                name: key,
                type: prop.type || (prop.$ref ? "Reference" : "unknown"),
                kind: "Property",
              });
            });
          }

          // Handle common nested structures in our data
          if (elements.length === 1 && selectedSchema.value.properties) {
            const topKey = Object.keys(selectedSchema.value.properties)[0];
            const topProp = selectedSchema.value.properties[topKey];
            if (topProp.properties) {
              Object.keys(topProp.properties).forEach((key) => {
                const prop = topProp.properties[key];
                elements.push({
                  name: `${topKey}.${key}`,
                  type: prop.type || (prop.$ref ? "Reference" : "unknown"),
                  kind: "Nested Property",
                });
              });
            }
          }

          return elements.length > 0 ? elements : null;
        } catch (e) {
          console.error("Error parsing JSON schema:", e);
          return null;
        }
      }

      return null;
    });

    return {
      allExperiments,
      activeSource,
      searchQuery,
      selectedSchema,
      selectedSchemaName,
      selectedSchemaProtocol,
      dataSources,
      filteredGroupedExperiments,
      showFutureFeatureAlert,
      showSchema,
      parsedSchemaElements,
    };
  },
}).mount("#app");

const { createApp, ref, computed, onMounted } = Vue;

createApp({
    setup() {
        const allExperiments = ref([]);
        const activeSource = ref('All');
        const searchQuery = ref('');

        const dataSources = computed(() => {
            const sources = allExperiments.value.map(exp => exp.data_sources || 'Unknown');
            return [...new Set(sources)].sort();
        });

        const filteredExperiments = computed(() => {
            let filtered = allExperiments.value;

            if (activeSource.value !== 'All') {
                filtered = filtered.filter(exp => (exp.data_sources || 'Unknown') === activeSource.value);
            }

            if (searchQuery.value.trim() !== '') {
                const query = searchQuery.value.toLowerCase();
                filtered = filtered.filter(exp => 
                    exp.bsd_document.toLowerCase().includes(query) || 
                    exp.primary_purpose.toLowerCase().includes(query) ||
                    (exp.notes && exp.notes.toLowerCase().includes(query))
                );
            }

            return filtered;
        });

        const filteredGroupedExperiments = computed(() => {
            const grouped = {};
            filteredExperiments.value.forEach(exp => {
                const source = exp.data_sources || 'Unknown';
                if (!grouped[source]) {
                    grouped[source] = [];
                }
                grouped[source].push(exp);
            });
            
            // Sort keys
            return Object.keys(grouped).sort().reduce((obj, key) => {
                obj[key] = grouped[key];
                return obj;
            }, {});
        });

        onMounted(async () => {
            try {
                const response = await fetch('data.json');
                allExperiments.value = await response.json();
            } catch (error) {
                console.error('Error loading data:', error);
            }
        });

        return {
            allExperiments,
            activeSource,
            searchQuery,
            dataSources,
            filteredGroupedExperiments
        };
    }
}).mount('#app');

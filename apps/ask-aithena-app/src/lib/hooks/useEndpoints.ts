import { useState, useEffect } from 'react';

interface Endpoints {
    apiUrl: string;
    rabbitmqWsUrl: string;
}

export function useEndpoints() {
    const [endpoints, setEndpoints] = useState<Endpoints | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchEndpoints() {
            try {
                const response = await fetch('/api/endpoints');
                if (!response.ok) {
                    throw new Error('Failed to fetch endpoints');
                }
                const data = await response.json();
                setEndpoints(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Unknown error');
            } finally {
                setLoading(false);
            }
        }

        fetchEndpoints();
    }, []);

    return { endpoints, error, loading };
} 
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
    baseURL: API_BASE_URL,
});

export const getStates = async () => {
    const response = await api.get('/states');
    return response.data.states;
};

export const getDistricts = async (state) => {
    const response = await api.get(`/districts/${state}`);
    return response.data.districts;
};

export const getForecasts = async (type, state, district) => {
    const params = {};
    if (state) params.state = state;
    if (district) params.district = district;

    const response = await api.get(`/forecasts/${type}`, { params });
    return response.data;
};

export const getRecommendations = async (state, district) => {
    const params = {};
    if (state) params.state = state;
    if (district) params.district = district;

    const response = await api.get('/recommendations', { params });
    return response.data;
};

export const getHeatmapData = async (type) => {
    const response = await api.get(`/heatmap/${type}`);
    return response.data;
};

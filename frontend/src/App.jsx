import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Register from './components/Register';
import Chat from './components/Chat';
import { authAPI } from './api';
import './App.css';

function App() {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const logoutTimerRef = useRef(null);

    // Check authentication status on mount
    useEffect(() => {
        const checkAuth = () => {
            const authenticated = authAPI.isAuthenticated();
            setIsAuthenticated(authenticated);

            if (authenticated) {
                setupAutoLogout();
            }

            setIsLoading(false);
        };

        checkAuth();
    }, []);

    // Setup auto-logout timer
    const setupAutoLogout = () => {
        // Clear existing timer
        if (logoutTimerRef.current) {
            clearTimeout(logoutTimerRef.current);
        }

        const expirationTime = authAPI.getTokenExpiration();
        if (!expirationTime) {
            handleLogout();
            return;
        }

        const currentTime = Date.now();
        const timeUntilExpiration = expirationTime - currentTime;

        // If token is already expired, logout immediately
        if (timeUntilExpiration <= 0) {
            handleLogout();
            return;
        }

        // Set timer to logout when token expires
        logoutTimerRef.current = setTimeout(() => {
            alert('Your session has expired. Please login again.');
            handleLogout();
        }, timeUntilExpiration);

        console.log(`Auto-logout scheduled in ${Math.round(timeUntilExpiration / 1000 / 60)} minutes`);
    };

    // Cleanup timer on unmount
    useEffect(() => {
        return () => {
            if (logoutTimerRef.current) {
                clearTimeout(logoutTimerRef.current);
            }
        };
    }, []);

    const handleLogin = () => {
        setIsAuthenticated(true);
        setupAutoLogout();
    };

    const handleLogout = () => {
        if (logoutTimerRef.current) {
            clearTimeout(logoutTimerRef.current);
        }
        authAPI.logout();
        setIsAuthenticated(false);
    };

    // Show loading while checking auth status
    if (isLoading) {
        return (
            <div style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: '100vh',
                fontSize: '1.5rem'
            }}>
                Loading...
            </div>
        );
    }

    return (
        <BrowserRouter>
            <Routes>
                <Route
                    path="/login"
                    element={!isAuthenticated ? <Login onLogin={handleLogin} /> : <Navigate to="/chat" />}
                />
                <Route
                    path="/register"
                    element={!isAuthenticated ? <Register onRegister={handleLogin} /> : <Navigate to="/chat" />}
                />
                <Route
                    path="/chat"
                    element={isAuthenticated ? <Chat onLogout={handleLogout} /> : <Navigate to="/login" />}
                />
                <Route
                    path="*"
                    element={<Navigate to={isAuthenticated ? "/chat" : "/login"} />}
                />
            </Routes>
        </BrowserRouter>
    );
}

export default App;

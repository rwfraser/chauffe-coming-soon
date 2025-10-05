// Simple blockchain client for controller name generation
// This file provides basic API interaction capabilities

class BlockchainClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }
    
    async generateControllerName(params) {
        try {
            const response = await fetch(`${this.baseUrl}/api/generate_controller_name`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(params)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error generating controller name:', error);
            throw error;
        }
    }
    
    async createBlockchain(name, dloidParams) {
        try {
            const response = await fetch(`${this.baseUrl}/api/create_blockchain`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: name,
                    dloid_params: dloidParams
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error creating blockchain:', error);
            throw error;
        }
    }
}

// Global instance
let blockchainClient = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Determine the appropriate API URL based on environment
    let apiUrl;
    
    if (window.location.hostname.includes('localhost') || window.location.hostname.includes('*********')) {
        // Development environment
        apiUrl = 'http://localhost:5000';
    } else {
        // Production environment - use relative URLs to work with Django
        apiUrl = '';
    }
        
    blockchainClient = new BlockchainClient(apiUrl);
});

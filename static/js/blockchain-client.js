// Simple blockchain client for controller name generation
// This file provides basic API interaction capabilities

class BlockchainClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.expectedApiVersion = '1.0.0'; // Expected CloudManager API version
        this.compatibleVersions = ['1.0.0', '1.0.1', '1.1.0']; // Compatible versions
        this.apiVersionChecked = false;
        this.apiCompatible = false;
        this.lastHealthCheck = null;
    }
    
    async checkApiHealth() {
        try {
            console.log('Checking CloudManager API health and version...');
            const response = await fetch(`${this.baseUrl}/api/health`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            
            if (!response.ok) {
                throw new Error(`Health check failed! HTTP ${response.status}: ${response.statusText}`);
            }
            
            const healthData = await response.json();
            this.lastHealthCheck = healthData;
            
            console.log('CloudManager Health Check:', healthData);
            
            // Check if version info is available
            if (healthData.version) {
                return this.validateApiVersion(healthData.version, healthData);
            } else {
                console.warn('CloudManager API does not provide version information');
                this.apiVersionChecked = true;
                this.apiCompatible = true; // Assume compatible if no version provided
                return {
                    success: true,
                    compatible: true, // Changed to true since API is working
                    message: 'API health OK (version unknown, assuming compatible)',
                    healthData: healthData,
                    version: 'unknown'
                };
            }
        } catch (error) {
            console.error('API health check failed:', error);
            return {
                success: false,
                compatible: false,
                error: error.message,
                message: `CloudManager API unavailable: ${error.message}`
            };
        }
    }
    
    validateApiVersion(apiVersion, healthData) {
        console.log(`CloudManager API Version: ${apiVersion}, Expected: ${this.expectedApiVersion}`);
        
        const isCompatible = this.compatibleVersions.includes(apiVersion);
        this.apiVersionChecked = true;
        this.apiCompatible = isCompatible;
        
        if (isCompatible) {
            return {
                success: true,
                compatible: true,
                version: apiVersion,
                message: `CloudManager API v${apiVersion} is compatible`,
                healthData: healthData
            };
        } else {
            const versionText = apiVersion || 'unknown';
            return {
                success: true,
                compatible: false,
                version: apiVersion,
                expectedVersions: this.compatibleVersions,
                message: `CloudManager API v${versionText} may not be compatible. Expected: ${this.compatibleVersions.join(', ')}`,
                healthData: healthData,
                warning: true
            };
        }
    }
    
    async testApiEndpoints() {
        console.log('Testing CloudManager API endpoints...');
        const testResults = {
            health: null,
            blockchains: null,
            createBlockchain: null,
            overall: 'unknown'
        };
        
        try {
            // Test 1: Health check
            testResults.health = await this.checkApiHealth();
            
            // Test 2: GET blockchains endpoint
            try {
                const response = await fetch(`${this.baseUrl}/api/blockchains`, {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    testResults.blockchains = {
                        success: true,
                        message: `Blockchains endpoint OK (${data.count || 0} blockchains)`,
                        data: data
                    };
                } else {
                    testResults.blockchains = {
                        success: false,
                        message: `Blockchains endpoint error: HTTP ${response.status}`,
                        status: response.status
                    };
                }
            } catch (error) {
                testResults.blockchains = {
                    success: false,
                    message: `Blockchains endpoint failed: ${error.message}`,
                    error: error.message
                };
            }
            
            // Test 3: POST blockchains endpoint (test creation with minimal data)
            try {
                const testPayload = {
                    name: `API Test ${new Date().toISOString()}`,
                    first_name: 'APITest',
                    last_name: 'User',
                    existing_licenses: 0,
                    user_uuid: '12345678-1234-5678-9abc-123456789abc', // Test UUID
                    dloid_params: {
                        firstName: 'APITest',
                        lastName: 'User',
                        priorDloidQty: '0',
                        chauffeQuantity: '0000100000',
                        partnershipStatus: 'L',
                        collateralizable: 'N',
                        inheritance: 'Y',
                        convertibility: '2',
                        rating: '000025000',
                        shareEligible: 'N',
                        redeemability: 'P'
                    }
                };
                
                const response = await fetch(`${this.baseUrl}/api/blockchains`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(testPayload)
                });
                
                if (response.ok) {
                    const data = await response.json();
                    testResults.createBlockchain = {
                        success: true,
                        message: 'Blockchain creation endpoint OK',
                        testBlockchainId: data.blockchain_id,
                        controllerGenerated: !!data.controller_name
                    };
                } else {
                    const errorText = await response.text();
                    testResults.createBlockchain = {
                        success: false,
                        message: `Blockchain creation failed: HTTP ${response.status}`,
                        status: response.status,
                        error: errorText
                    };
                }
            } catch (error) {
                testResults.createBlockchain = {
                    success: false,
                    message: `Blockchain creation test failed: ${error.message}`,
                    error: error.message
                };
            }
            
            // Determine overall status
            const allTests = [testResults.health, testResults.blockchains, testResults.createBlockchain];
            const successCount = allTests.filter(test => test?.success).length;
            
            if (successCount === 3) {
                testResults.overall = 'success';
            } else if (successCount >= 2) {
                testResults.overall = 'warning';
            } else {
                testResults.overall = 'failure';
            }
            
        } catch (error) {
            console.error('API endpoint testing failed:', error);
            testResults.overall = 'failure';
            testResults.error = error.message;
        }
        
        console.log('API Test Results:', testResults);
        return testResults;
    }
    
    async createBlockchain(name, dloidParams, userUuid = null) {
        const endpoint = `${this.baseUrl}/api/blockchains`;
        console.log('=== BLOCKCHAIN CREATION DEBUG ===');
        console.log('Endpoint URL:', endpoint);
        console.log('Method: POST');
        console.log('Payload:', { name, first_name: dloidParams.firstName, last_name: dloidParams.lastName, user_uuid: userUuid });
        console.log('Full dloidParams:', dloidParams);
        
        // Validate required user UUID
        if (!userUuid) {
            throw new Error('user_uuid is required for blockchain creation');
        }
        
        // Check API version if not already done
        if (!this.apiVersionChecked) {
            console.log('Performing API version check before blockchain creation...');
            const versionCheck = await this.checkApiHealth();
            if (!versionCheck.success) {
                throw new Error(`CloudManager API unavailable: ${versionCheck.message}`);
            }
            if (versionCheck.warning) {
                console.warn('Version compatibility warning:', versionCheck.message);
                // Don't throw error for version warnings, just log them
            }
            console.log(`API version check complete. Compatible: ${versionCheck.compatible}, Version: ${versionCheck.version || 'unknown'}`);
        }
        
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: name,
                    first_name: dloidParams.firstName,
                    last_name: dloidParams.lastName,
                    existing_licenses: parseInt(dloidParams.priorDloidQty) || 0,
                    user_uuid: userUuid,
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
        // Production environment - use CloudManager.py on Fly.io
        apiUrl = 'https://pychain.fly.dev';
    }
        
    blockchainClient = new BlockchainClient(apiUrl);
});

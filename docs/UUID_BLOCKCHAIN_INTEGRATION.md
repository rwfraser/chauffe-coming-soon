# UUID and Blockchain Integration

## Overview
Each user in the My Chauffe platform now has a unique UUID that definitively links their website account with their DLOIDs and blockchain controllers.

## Implementation Details

### 1. UUID Field Addition
- Added a `uuid` field to the `UserProfile` model
- UUID is automatically generated using `uuid.uuid4()`
- Field is unique, non-editable, and set as default on creation
- All existing users received UUIDs through a custom migration

### 2. Automatic Profile Creation
- Implemented Django signals in `accounts/signals.py` to automatically create UserProfile instances
- Profile creation happens when a User account is created
- Handles both new registrations and existing users

### 3. User Interface Integration
- UUID is displayed in the user's profile page (`/accounts/profile/`)
- UUID is shown in a dedicated "Account Information" section
- Includes a "Copy" button with JavaScript functionality for easy copying
- UUID is displayed in monospace font for better readability

### 4. Blockchain Reference Storage
- Added `blockchain_references` TextField to store DLOID and blockchain info as JSON
- Methods to add and retrieve blockchain references:
  - `add_blockchain_reference(dloid, blockchain_info)` - Add new DLOID/blockchain mapping
  - `get_blockchain_references()` - Retrieve all blockchain references
  - `get_uuid_string()` - Get UUID as string for blockchain operations

### 5. Database Schema Changes
Three migrations were created:
1. `0002_userprofile_uuid.py` - Adds UUID field with proper unique value generation for existing users
2. `0003_userprofile_blockchain_references.py` - Adds blockchain reference storage

## Usage Examples

### Getting a User's UUID
```python
# Via UserProfile
user_profile = UserProfile.objects.get(user=request.user)
uuid_string = user_profile.get_uuid_string()

# Direct access
uuid_string = str(request.user.profile.uuid)
```

### Adding Blockchain References
```python
user_profile = request.user.profile
user_profile.add_blockchain_reference(
    'DLOID123',
    {
        'chain_id': 'ethereum',
        'contract_address': '0x1234...',
        'controller_name': 'MyController'
    }
)
```

### Retrieving Blockchain References
```python
references = user_profile.get_blockchain_references()
for dloid, info in references.items():
    print(f"DLOID: {dloid}, Chain: {info['blockchain_info']['chain_id']}")
```

## Security Considerations
- UUIDs are unique and non-guessable, providing secure identification
- UUIDs are visible to users in their profile for reference but not exposed in URLs
- Blockchain references are stored securely and only accessible to the user
- UUIDs cannot be changed once created, ensuring permanent account linking

## Integration Points
This UUID system is designed to integrate with:
1. DLOID generation systems
2. Blockchain controller creation
3. License management
4. Transaction tracking
5. External blockchain services

## Files Modified
- `core/models.py` - Added UUID field and blockchain reference functionality
- `accounts/signals.py` - New file for automatic profile creation
- `accounts/apps.py` - Updated to register signals
- `templates/accounts/profile.html` - Added UUID display section
- `core/migrations/0002_userprofile_uuid.py` - UUID field migration
- `core/migrations/0003_userprofile_blockchain_references.py` - Blockchain references migration

## Future Enhancements
- API endpoints to query users by UUID
- Integration with blockchain monitoring services
- Automated DLOID generation using UUIDs
- Backup and recovery procedures for blockchain references
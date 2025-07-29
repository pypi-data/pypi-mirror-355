# Nucleation PHP Extension Installation

## Requirements
- PHP 8.2+ 
- Platform: linux-x64

## Installation

### Automatic Installation (Recommended)
```bash
# Download and run install script
curl -sSL https://install.nucleation.dev/php | bash
```

### Manual Installation

1. Copy the extension file to your PHP extensions directory:
   ```bash
   sudo cp nucleation-php8.2-linux-x64.so $(php-config --extension-dir)/nucleation.so
   ```

2. Add to your php.ini or create a conf.d file:
   ```bash
   echo "extension=nucleation.so" | sudo tee $(php --ini | grep "Scan for additional" | cut -d: -f2 | xargs)/20-nucleation.ini
   ```

3. Restart your web server/PHP-FPM:
   ```bash
   # For Apache
   sudo systemctl restart apache2
   # For Nginx + PHP-FPM
   sudo systemctl restart php8.2-fpm nginx
   # For development server
   # No restart needed
   ```

4. Verify installation:
   ```bash
   php -m | grep nucleation
   php -r "var_dump(nucleation_version());"
   php -r "echo nucleation_hello();"
   ```

## IDE Support

Include `nucleation-stubs.php` in your project for full IDE autocompletion:

```php
<?php
// At the top of your PHP files or in your IDE configuration
require_once 'path/to/nucleation-stubs.php';

// Now you get full autocompletion
$schematic = new Nucleation\Schematic("MyBuilding");
$schematic->loadFromData($data); // <- IDE autocompletes this
```

## Usage Examples

```php
<?php

// Basic usage
$schematic = new Nucleation\Schematic("CoolBuild");
$schematic->setMetadataAuthor("Builder123");

// Load from file
$data = file_get_contents("build.litematic");
$schematic->loadFromData($data);

// Get info
$info = $schematic->getInfo();
echo "Blocks: " . $schematic->getBlockCount() . PHP_EOL;

// Convert formats
$inputData = file_get_contents("input.schem");
$litematicData = nucleation_convert_format($inputData, "litematic");
file_put_contents("output.litematic", $litematicData);
```

import sharp from 'sharp';
import fs from 'fs';

async function run() {
  await sharp('demos/latest/gallery/01-operator-dashboard-overview.png')
    .resize(640, 360, { fit: 'cover' })
    .webp({ quality: 85 })
    .toFile('/Users/jarad/git/netfix/thumbnails/sm3.webp');
  
  if (fs.existsSync('/Users/jarad/git/netfix/beta-livive-net/thumbnails')) {
    fs.copyFileSync('/Users/jarad/git/netfix/thumbnails/sm3.webp', '/Users/jarad/git/netfix/beta-livive-net/thumbnails/sm3.webp');
  }
  if (fs.existsSync('/Users/jarad/git/netfix/livive-net/thumbnails')) {
    fs.copyFileSync('/Users/jarad/git/netfix/thumbnails/sm3.webp', '/Users/jarad/git/netfix/livive-net/thumbnails/sm3.webp');
  }
  console.log("Generated thumbnails/sm3.webp successfully!");
}

run().catch(console.error);

#!/usr/bin/env node

/**
 * Rico System V5 - Markdown to PDF Pipeline
 * Konvertiert Markdown-Dateien in docs/ zu PDFs in docs/pdf/
 */

const { mdToPdf } = require('md-to-pdf');
const { globby } = require('globby');
const fs = require('fs-extra');
const path = require('path');

// Konfiguration
const CONFIG = {
  docsDir: 'docs',
  pdfDir: 'docs/pdf',
  configFile: 'docs/_pdf_config.json',
  stylesheet: 'docs/_pdf_theme.css',
  excludePatterns: ['docs/pdf/**', 'docs/_*.md']
};

// CLI Argumente parsen
function parseArgs() {
  const args = process.argv.slice(2);
  const mode = args[0];
  const filePath = args[1];
  
  if (mode === '--all') {
    return { mode: 'all' };
  } else if (mode === '--file' && filePath) {
    return { mode: 'file', filePath };
  } else {
    console.error('❌ Ungültige Argumente. Verwendung:');
    console.error('  npm run pdf:all     # Alle Markdown-Dateien konvertieren');
    console.error('  npm run pdf:one --file <pfad>  # Einzelne Datei konvertieren');
    process.exit(1);
  }
}

// PDF-Konfiguration laden
async function loadConfig() {
  let config = {};
  
  try {
    if (await fs.pathExists(CONFIG.configFile)) {
      const configData = await fs.readJson(CONFIG.configFile);
      config = { ...config, ...configData };
    }
  } catch (error) {
    console.warn('⚠️  Konfigurationsdatei nicht gefunden, verwende Standardwerte');
  }
  
  // Standard-Konfiguration
  const defaultConfig = {
    launch_options: {
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    },
    pdf_options: {
      format: 'A4',
      margin: {
        top: '18mm',
        right: '14mm',
        bottom: '22mm',
        left: '14mm'
      },
      printBackground: true
    },
    stylesheet: CONFIG.stylesheet,
    body_class: 'rico-doc',
    marked_options: {
      gfm: true,
      breaks: false
    },
    md_file_encoding: 'utf-8'
  };
  
  return { ...defaultConfig, ...config };
}

// Markdown-Dateien finden
async function findMarkdownFiles() {
  const patterns = [
    `${CONFIG.docsDir}/**/*.md`,
    `!${CONFIG.docsDir}/pdf/**`,
    `!${CONFIG.docsDir}/_*.md`
  ];
  
  const files = await globby(patterns);
  return files.filter(file => !file.includes('/pdf/') && !file.includes('/_'));
}

// Einzelne Datei konvertieren
async function convertFile(inputPath, config) {
  try {
    const fileName = path.basename(inputPath, '.md');
    const outputPath = path.join(CONFIG.pdfDir, `${fileName}.pdf`);
    
    console.log(`📄 Konvertiere: ${inputPath} → ${outputPath}`);
    
    const pdf = await mdToPdf(
      { path: inputPath },
      {
        ...config,
        dest: outputPath
      }
    );
    
    if (pdf) {
      console.log(`✅ Erfolgreich: ${outputPath}`);
      return { success: true, input: inputPath, output: outputPath };
    } else {
      throw new Error('PDF-Generierung fehlgeschlagen');
    }
  } catch (error) {
    console.error(`❌ Fehler bei ${inputPath}:`, error.message);
    return { success: false, input: inputPath, error: error.message };
  }
}

// Front-Matter parsen (einfache YAML-Erkennung)
function parseFrontMatter(content) {
  const frontMatterRegex = /^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/;
  const match = content.match(frontMatterRegex);
  
  if (match) {
    const yamlContent = match[1];
    const markdownContent = match[2];
    
    // Einfache YAML-Parsing (nur für title, subtitle, author, date)
    const frontMatter = {};
    yamlContent.split('\n').forEach(line => {
      const [key, ...valueParts] = line.split(':');
      if (key && valueParts.length > 0) {
        const value = valueParts.join(':').trim().replace(/^["']|["']$/g, '');
        frontMatter[key.trim()] = value;
      }
    });
    
    return { frontMatter, content: markdownContent };
  }
  
  return { frontMatter: null, content };
}

// Deckblatt HTML generieren
function generateCoverPage(frontMatter) {
  if (!frontMatter || !frontMatter.title) return '';
  
  const { title, subtitle, author, date } = frontMatter;
  
  return `
    <div class="cover-page">
      <div class="cover-content">
        <h1 class="cover-title">${title}</h1>
        ${subtitle ? `<h2 class="cover-subtitle">${subtitle}</h2>` : ''}
        ${author ? `<p class="cover-author">${author}</p>` : ''}
        ${date ? `<p class="cover-date">${date}</p>` : ''}
      </div>
    </div>
    <div class="page-break"></div>
  `;
}

// Hauptfunktion
async function main() {
  const startTime = Date.now();
  const args = parseArgs();
  
  console.log('🚀 Rico System V5 - PDF Pipeline gestartet');
  
  try {
    // PDF-Verzeichnis erstellen
    await fs.ensureDir(CONFIG.pdfDir);
    
    // Konfiguration laden
    const config = await loadConfig();
    
    let files = [];
    let results = [];
    
    if (args.mode === 'all') {
      // Alle Markdown-Dateien finden
      files = await findMarkdownFiles();
      console.log(`📁 Gefunden: ${files.length} Markdown-Dateien`);
    } else if (args.mode === 'file') {
      // Einzelne Datei
      if (!await fs.pathExists(args.filePath)) {
        console.error(`❌ Datei nicht gefunden: ${args.filePath}`);
        process.exit(1);
      }
      files = [args.filePath];
    }
    
    if (files.length === 0) {
      console.log('ℹ️  Keine Markdown-Dateien gefunden');
      return;
    }
    
    // Dateien konvertieren
    for (const file of files) {
      const result = await convertFile(file, config);
      results.push(result);
    }
    
    // Ergebnisse zusammenfassen
    const successful = results.filter(r => r.success);
    const failed = results.filter(r => !r.success);
    
    const duration = ((Date.now() - startTime) / 1000).toFixed(1);
    
    console.log('\n📊 Zusammenfassung:');
    console.log(`✅ Erfolgreich: ${successful.length}`);
    console.log(`❌ Fehlgeschlagen: ${failed.length}`);
    console.log(`⏱️  Dauer: ${duration}s`);
    
    if (failed.length > 0) {
      console.log('\n❌ Fehlgeschlagene Dateien:');
      failed.forEach(f => console.log(`  - ${f.input}: ${f.error}`));
      process.exit(1);
    }
    
    console.log('\n🎉 PDF-Pipeline erfolgreich abgeschlossen!');
    
  } catch (error) {
    console.error('💥 Kritischer Fehler:', error.message);
    process.exit(1);
  }
}

// Script ausführen
if (require.main === module) {
  main().catch(error => {
    console.error('💥 Unbehandelter Fehler:', error);
    process.exit(1);
  });
}

module.exports = { convertFile, loadConfig, findMarkdownFiles };

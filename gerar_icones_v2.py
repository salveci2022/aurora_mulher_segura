#!/usr/bin/env python3
# ============================================
# GERADOR DE ÍCONES - AURORA MULHER SEGURA
# VERSÃO 2.0 - COM VERIFICAÇÃO MELHORADA
# ============================================

from PIL import Image
import os
import sys

def main():
    print("=" * 60)
    print("🌸 AURORA MULHER SEGURA - GERADOR DE ÍCONES v2.0")
    print("=" * 60)
    
    # Pasta de trabalho
    pasta_img = "static/img"
    
    # Cria pasta se não existir
    if not os.path.exists(pasta_img):
        print(f"📁 Criando pasta: {pasta_img}")
        os.makedirs(pasta_img)
    
    # Procura a logo
    logo_file = None
    possiveis_nomes = [
        "logo.png",
        "logo.jpg", 
        "icon.png",
        "favicon.png",
        "aurora.png"
    ]
    
    print("\n🔍 Procurando logo...")
    for nome in possiveis_nomes:
        caminho = os.path.join(pasta_img, nome)
        if os.path.exists(caminho):
            logo_file = caminho
            print(f"✅ Encontrada: {nome}")
            break
    
    if not logo_file:
        print("\n❌ ERRO: Logo não encontrada!")
        print(f"\n📂 Procurei em: {os.path.abspath(pasta_img)}")
        print("\n📝 Arquivos procurados:")
        for nome in possiveis_nomes:
            print(f"   - {nome}")
        
        # Lista o que tem na pasta
        if os.path.exists(pasta_img):
            arquivos = os.listdir(pasta_img)
            if arquivos:
                print(f"\n📄 Arquivos encontrados na pasta:")
                for arq in arquivos:
                    print(f"   - {arq}")
            else:
                print(f"\n⚠️  Pasta está VAZIA!")
        else:
            print(f"\n⚠️  Pasta NÃO EXISTE!")
        
        print("\n💡 SOLUÇÃO:")
        print("1. Coloque sua logo.png na pasta static/img/")
        print("2. Ou execute: python gerar_icones_v2.py caminho/da/sua/logo.png")
        return False
    
    # Tenta abrir a imagem
    try:
        print(f"\n🖼️  Abrindo imagem: {logo_file}")
        img = Image.open(logo_file)
        print(f"✅ Imagem aberta com sucesso!")
        print(f"📐 Tamanho: {img.size[0]}x{img.size[1]} pixels")
        print(f"🎨 Modo: {img.mode}")
    except Exception as e:
        print(f"\n❌ ERRO ao abrir imagem: {e}")
        print("\n💡 A imagem pode estar corrompida ou em formato inválido.")
        print("💡 Tente converter para PNG usando um conversor online.")
        return False
    
    # Tamanhos a gerar
    tamanhos = {
        'icon-72.png': 72,
        'icon-96.png': 96,
        'icon-128.png': 128,
        'icon-144.png': 144,
        'icon-152.png': 152,
        'icon-192.png': 192,
        'icon-384.png': 384,
        'icon-512.png': 512,
        'favicon.png': 32
    }
    
    print(f"\n📦 Gerando {len(tamanhos)} ícones...")
    print("-" * 60)
    
    # Converte para RGB se necessário (PNG com transparência)
    if img.mode in ('RGBA', 'P', 'LA'):
        print("🎨 Convertendo para RGB...")
        img_rgb = img.convert('RGB')
    else:
        img_rgb = img
    
    # Gera cada tamanho
    gerados = 0
    for nome, tamanho in tamanhos.items():
        try:
            # Redimensiona
            img_resized = img_rgb.resize((tamanho, tamanho), Image.Resampling.LANCZOS)
            
            # Salva
            caminho_saida = os.path.join(pasta_img, nome)
            img_resized.save(caminho_saida, 'PNG', optimize=True, quality=95)
            
            print(f"✅ {nome:20s} - {tamanho}x{tamanho}px")
            gerados += 1
            
        except Exception as e:
            print(f"❌ Erro ao gerar {nome}: {e}")
    
    # Resumo
    print("-" * 60)
    print(f"\n🎉 CONCLUÍDO!")
    print(f"✅ {gerados}/{len(tamanhos)} ícones gerados")
    print(f"📁 Pasta: {os.path.abspath(pasta_img)}")
    
    if gerados == len(tamanhos):
        print("\n✨ Todos os ícones foram gerados com sucesso!")
        return True
    else:
        print(f"\n⚠️ {len(tamanhos) - gerados} falharam")
        return False

if __name__ == "__main__":
    # Verifica Pillow
    try:
        from PIL import Image
    except ImportError:
        print("❌ ERRO: Pillow não instalado!")
        print("\nInstale com:")
        print("pip install Pillow")
        sys.exit(1)
    
    # Executa
    sucesso = main()
    
    if sucesso:
        print("\n" + "=" * 60)
        print("✅ PRONTO! Ícones gerados em static/img/")
        print("=" * 60)
    else:
        sys.exit(1)
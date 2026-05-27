- name: Extract text and images
        run: |
          python3 << 'EOF'
          import fitz, os
          
          doc = fitz.open("LLM.pdf")
          os.makedirs("images", exist_ok=True)
          
          # 提取文字，遇到图片插入引用链接
          text = ""
          img_count = 0
          for page_num, page in enumerate(doc):
              text += f"\n\n## Page {page_num+1}\n"
              text += page.get_text()
              
              # 提取该页所有图片
              for img in page.get_images():
                  xref = img[0]
                  pix = fitz.Pixmap(doc, xref)
                  img_name = f"images/fig_p{page_num+1}_{img_count}.png"
                  if pix.n > 4:
                      pix = fitz.Pixmap(fitz.csRGB, pix)
                  pix.save(img_name)
                  text += f"\n![图片]({img_name})\n"
                  img_count += 1
          
          with open("paper.md", "w", encoding="utf-8") as f:
              f.write(text)
          print(f"完成：{len(doc)}页，{img_count}张图片")
          EOF

      - name: Commit
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add paper.md images/
          git commit -m "Add paper text and images"
          git push

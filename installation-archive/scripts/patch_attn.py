path = r"C:\Users\user\TouchDesigner\StreamDiffusionTD\StreamDiffusionTD031\StreamDiffusion\venv\Lib\site-packages\diffusers_ipadapter\ip_adapter\attention_processor.py"

with open(path, 'r') as f:
    content = f.read()

old = """        # for ip-adapter
        ip_key = self.to_k_ip(ip_hidden_states)
        ip_value = self.to_v_ip(ip_hidden_states)
        
        ip_key = attn.head_to_batch_dim(ip_key)
        ip_value = attn.head_to_batch_dim(ip_value)
        
        ip_attention_probs = attn.get_attention_scores(query, ip_key, None)
        ip_hidden_states = torch.bmm(ip_attention_probs, ip_value)
        ip_hidden_states = attn.batch_to_head_dim(ip_hidden_states)"""

new = """        # for ip-adapter
        ip_key = self.to_k_ip(ip_hidden_states)
        ip_value = self.to_v_ip(ip_hidden_states)
        
        ip_key = attn.head_to_batch_dim(ip_key)
        ip_value = attn.head_to_batch_dim(ip_value)
        
        # Cast to float32 to prevent NaN/overflow in float16 attention
        _dtype = hidden_states.dtype
        ip_attention_probs = attn.get_attention_scores(query.float(), ip_key.float(), None)
        ip_hidden_states = torch.bmm(ip_attention_probs, ip_value.float())
        ip_hidden_states = ip_hidden_states.to(_dtype)
        ip_hidden_states = attn.batch_to_head_dim(ip_hidden_states)"""

if old in content:
    content = content.replace(old, new)
    print("Patch applied")
else:
    # Try with different whitespace
    print("Pattern not found exactly, checking...")
    print(repr(content[content.find("# for ip-adapter"):content.find("# for ip-adapter")+400]))

with open(path, 'w') as f:
    f.write(content)

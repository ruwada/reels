from g import run
R='/mnt/project-files/reels/smeshnye/referensy-2/'
F=[R+'01-anfas.jpg',R+'02-anfas-2.jpg']
T=[R+'04-vpoloborota-vpravo.jpg',R+'05-vpoloborota-vlevo.jpg']
base=("The reference photos all show the same real man. Create a NEW photo of exactly this man. His face must be identical to the references: same eyes, eyebrows, nose shape and width, cheeks, skin texture with small marks, long thick curly black beard, same face width. Do not beautify, do not make the face slimmer or younger, no smoothing. "
"Ultra-realistic photograph, looks like a real frame from a cinematic thriller shot on a real camera, true-to-life skin, no CGI look. Vertical 9:16. "
"He is the only person in the frame. No women. No necklace, nothing around the neck. "
"Outfit: plain black hoodie (hood down) and a black knit beanie. ")
S=[
('01-planshet', F+[T[0]], "Setting: a dark server room at night, rows of server racks with small blue and amber indicator lights, shallow depth of field, cold blue haze. Medium close-up, chest up. He holds a tablet in both hands at chest height, the screen faces him and lights his face with cool blue light. He looks straight into the camera, serious and calm, mouth closed. Leave dark empty space above his head for text."),
('02-noutbuk', F+[T[1]], "Setting: a dark home office at night. He sits at a desk in front of an open ordinary black Windows laptop (NOT a MacBook, no Apple logo), the screen glow is warm amber on his face. Medium shot from slightly in front and to the side so both his face and the laptop keyboard are visible. He has just turned his head from the screen to look straight into the camera with a questioning, slightly raised eyebrow, mouth closed. Leave dark empty space in the upper part of the frame for text."),
]
run([(n,refs,base+p) for n,refs,p in S])

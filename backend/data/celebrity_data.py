"""
Celebrity data pools, A-list definitions, aliases, and categories
"""

# LARGE CELEBRITY POOLS - 50+ celebrities per category to pull from
CELEBRITY_POOLS = {
    "movie_stars": [
        # Current A-listers
        "Tom Holland", "Florence Pugh", "Idris Elba", "Emily Blunt", "Dev Patel",
        "Leonardo DiCaprio", "Brad Pitt", "Angelina Jolie", "Tom Cruise", "Jennifer Lawrence",
        "Margot Robbie", "Ryan Gosling", "Emma Stone", "Chris Hemsworth", "Scarlett Johansson",
        "Robert Downey Jr", "Chris Evans", "Zendaya", "Timothee Chalamet", "Sydney Sweeney",
        "Ana de Armas", "Austin Butler", "Jacob Elordi", "Glen Powell", "Jenna Ortega",
        "Anya Taylor-Joy", "Paul Mescal", "Barry Keoghan", "Daisy Edgar-Jones", "Josh O'Connor",
        "Cillian Murphy", "Dakota Johnson", "Pedro Pascal", "Oscar Isaac", "Florence Pugh",
        "Jason Momoa", "Gal Gadot", "Henry Cavill", "Dwayne Johnson", "Vin Diesel",
        "Keanu Reeves", "Sandra Bullock", "Julia Roberts", "George Clooney", "Matt Damon",
        "Ben Affleck", "Jennifer Garner", "Reese Witherspoon", "Nicole Kidman", "Cate Blanchett",
        "Meryl Streep", "Viola Davis", "Denzel Washington", "Samuel L Jackson", "Morgan Freeman",
        "Al Pacino", "Robert De Niro", "Michael Caine", "Anthony Hopkins", "Ian McKellen",
        "Patrick Stewart", "Judi Dench", "Helen Mirren", "Emma Thompson", "Kate Winslet",
        "Rachel McAdams", "Anne Hathaway", "Natalie Portman", "Keira Knightley", "Saoirse Ronan",
        # More stars
        "Chris Pratt", "Ryan Reynolds", "Hugh Jackman", "Mark Wahlberg", "Will Smith",
        "Johnny Depp", "Tom Hanks", "Harrison Ford", "Michael B Jordan", "John Boyega",
        "Lupita Nyongo", "Awkwafina", "Simu Liu", "Gemma Chan", "Michelle Yeoh",
        "Jamie Lee Curtis", "Brendan Fraser", "Ke Huy Quan", "Jessica Chastain", "Julianne Moore",
        "Amy Adams", "Emily Ratajkowski", "Hailee Steinfeld", "Elle Fanning", "Dakota Fanning"
    ],
    "tv_actors": [
        # British TV
        "Jenna Coleman", "Jodie Comer", "Richard Madden", "Ncuti Gatwa", "Olivia Colman",
        "David Tennant", "Matt Smith", "Peter Capaldi", "Jodie Whittaker", "Karen Gillan",
        "Suranne Jones", "Martin Compston", "Vicky McClure", "Adrian Dunbar", "Keeley Hawes",
        "Ruth Wilson", "Dominic West", "Gillian Anderson", "Jamie Dornan", "Cush Jumbo",
        "David Oyelowo", "Thandiwe Newton", "Michaela Coel", "Phoebe Waller-Bridge", "Andrew Scott",
        "Fleabag", "Rosamund Pike", "Maxine Peake", "Sheridan Smith", "Sarah Lancashire",
        "Stephen Graham", "Sean Bean", "Jason Statham", "Gemma Arterton", "Naomie Harris",
        "Michelle Keegan",  # Coronation Street, Our Girl, Brassic
        # US TV
        "Kit Harington", "Emilia Clarke", "Sophie Turner", "Maisie Williams", "Nikolaj Coster-Waldau",
        "Bryan Cranston", "Aaron Paul", "Elisabeth Moss", "Steve Carell", "Jenna Fischer",
        "Rainn Wilson", "John Krasinski", "Sarah Snook", "Jeremy Strong", "Brian Cox",
        "Matthew Macfadyen", "Kieran Culkin", "Jason Sudeikis", "Hannah Waddingham", "Brett Goldstein",
        "Zooey Deschanel", "Kaley Cuoco", "Jim Parsons", "Johnny Galecki", "Kunal Nayyar",
        "Jennifer Aniston", "Courteney Cox", "Lisa Kudrow", "Matt LeBlanc", "David Schwimmer",
        "Sofia Vergara", "Julie Bowen", "Ty Burrell", "Jesse Tyler Ferguson", "Eric Stonestreet",
        "Zach Braff", "Donald Faison", "Neil Patrick Harris", "Jason Segel", "Alyson Hannigan"
    ],
    "musicians": [
        # Current pop stars
        "Dua Lipa", "Ed Sheeran", "Adele", "Harry Styles", "Stormzy",
        "Taylor Swift", "Beyonce", "Rihanna", "Lady Gaga", "Ariana Grande",
        "Billie Eilish", "Olivia Rodrigo", "Doja Cat", "SZA", "Lizzo",
        "Post Malone", "Bad Bunny", "Drake", "Kendrick Lamar", "Travis Scott",
        "The Weeknd", "Bruno Mars", "Justin Bieber", "Shawn Mendes", "Charlie Puth",
        "Sam Smith", "Lewis Capaldi", "Tom Grennan", "George Ezra", "Rag'n'Bone Man",
        # UK legends
        "Elton John", "Paul McCartney", "Mick Jagger", "Rod Stewart", "Ozzy Osbourne",
        "Noel Gallagher", "Liam Gallagher", "Robbie Williams", "Gary Barlow", "Olly Murs",
        "Rita Ora", "Jessie J", "Anne-Marie", "Ellie Goulding", "Dua Lipa",
        "Florence Welch", "Leona Lewis", "Cheryl Cole", "Nicole Scherzinger", "Mel B",
        # US & International
        "Cardi B", "Megan Thee Stallion", "Nicki Minaj", "Ice Spice", "Latto",
        "Miley Cyrus", "Selena Gomez", "Demi Lovato", "Katy Perry", "Pink",
        "Justin Timberlake", "Usher", "Chris Brown", "Jason Derulo", "Ne-Yo",
        "Kanye West", "Jay-Z", "Eminem", "50 Cent", "Snoop Dogg",
        "Liza Minnelli", "Cher", "Madonna", "Britney Spears", "Christina Aguilera",
        "Shakira", "Jennifer Lopez", "Mariah Carey", "Celine Dion", "Whitney Houston"
    ],
    "athletes": [
        # Football
        "Harry Kane", "Marcus Rashford", "Raheem Sterling", "Jude Bellingham", "Phil Foden",
        "Bukayo Saka", "Jack Grealish", "Mason Mount", "Declan Rice", "Trent Alexander-Arnold",
        "Mo Salah", "Virgil van Dijk", "Erling Haaland", "Kevin De Bruyne", "Bruno Fernandes",
        "Cristiano Ronaldo", "Lionel Messi", "Neymar", "Kylian Mbappe", "Robert Lewandowski",
        "David Beckham", "Wayne Rooney", "Steven Gerrard", "Frank Lampard", "John Terry",
        "Gary Lineker", "Alan Shearer", "Michael Owen", "Rio Ferdinand", "Paul Scholes",
        # Tennis
        "Andy Murray", "Roger Federer", "Rafael Nadal", "Novak Djokovic", "Emma Raducanu",
        "Serena Williams", "Venus Williams", "Naomi Osaka", "Coco Gauff", "Maria Sharapova",
        # Other sports
        "Lewis Hamilton", "Max Verstappen", "Lando Norris", "George Russell", "Daniel Ricciardo",
        "Usain Bolt", "Mo Farah", "Jessica Ennis-Hill", "Dina Asher-Smith", "Katarina Johnson-Thompson",
        "Anthony Joshua", "Tyson Fury", "Conor McGregor", "Floyd Mayweather", "Mike Tyson",
        "LeBron James", "Steph Curry", "Kevin Durant", "Michael Jordan", "Kobe Bryant",
        "Tom Brady", "Patrick Mahomes", "Simone Biles", "Michael Phelps", "Adam Peaty"
    ],
    "royals": [
        # British Royal Family
        "King Charles III", "Queen Camilla", "Prince William", "Catherine Princess of Wales",
        "Prince Harry", "Meghan Markle", "Prince George", "Princess Charlotte", "Prince Louis",
        "Princess Anne", "Prince Andrew", "Prince Edward", "Sophie Duchess of Edinburgh",
        "Princess Beatrice", "Princess Eugenie", "Zara Tindall", "Peter Phillips",
        "Lady Louise Windsor", "James Viscount Severn", "Sarah Ferguson",
        "Archie Mountbatten-Windsor", "Lilibet Mountbatten-Windsor",
        "Mike Tindall", "Edoardo Mapelli Mozzi", "Jack Brooksbank",
        # Historical
        "Queen Elizabeth II", "Princess Diana", "Prince Philip",
        # European Royals
        "King Felipe VI of Spain", "Queen Letizia of Spain",
        "King Willem-Alexander of Netherlands", "Queen Maxima of Netherlands",
        "Crown Princess Victoria of Sweden", "Prince Daniel of Sweden",
        "Crown Princess Mary of Denmark", "King Frederik X of Denmark",
        "Prince Albert of Monaco", "Princess Charlene of Monaco",
        "King Carl XVI Gustaf of Sweden", "Queen Silvia of Sweden"
    ],
    "reality_tv": [
        # TOWIE & UK Reality
        "Katie Price", "Gemma Collins", "Pete Wicks", "Joey Essex", "Sam Faiers",
        "Mark Wright", "Amy Childs", "Lauren Goodger", "Billie Faiers",
        "Vicky Pattison", "Charlotte Crosby", "Holly Hagan", "Chloe Ferry", "Marnie Simpson",
        # Made in Chelsea
        "Georgia Toffolo", "Jamie Laing", "Spencer Matthews", "Binky Felstead",
        "Ollie Locke", "Sam Thompson", "Zara McDermott", "Lucy Watson", "Proudlock",
        # Love Island UK
        "Molly-Mae Hague", "Tommy Fury", "Maura Higgins", "Amber Gill", "Dani Dyer",
        "Jack Fincham", "Ekin-Su Culculoglu", "Davide Sanclimenti", "Olivia Attwood",
        "Amber Davies", "Kem Cetinay", "Cara De La Hoyde", "Nathan Massey", "Olivia Buckland",
        # Kardashians & US Reality
        "Kim Kardashian", "Khloe Kardashian", "Kourtney Kardashian", "Kylie Jenner", "Kendall Jenner",
        "Kris Jenner", "Scott Disick", "Travis Barker", "Paris Hilton", "Nicole Richie",
        "Lauren Conrad", "Kristin Cavallari", "Spencer Pratt", "Heidi Montag", "Brody Jenner",
        "Lisa Vanderpump", "Kyle Richards", "Teresa Giudice", "NeNe Leakes", "Bethenny Frankel"
    ],
    "public_figure": [
        # Tech billionaires
        "Elon Musk", "Mark Zuckerberg", "Jeff Bezos", "Bill Gates", "Tim Cook",
        "Sundar Pichai", "Satya Nadella", "Jack Dorsey", "Reed Hastings", "Jensen Huang",
        # US Politicians
        "Donald Trump", "Joe Biden", "Barack Obama", "Michelle Obama", "Hillary Clinton",
        "Nancy Pelosi", "Alexandria Ocasio-Cortez", "Bernie Sanders", "Kamala Harris", "Mike Pence",
        # UK Politicians
        "Boris Johnson", "Rishi Sunak", "Keir Starmer", "Nigel Farage", "Liz Truss",
        "Theresa May", "David Cameron", "Tony Blair", "Jeremy Corbyn", "Sadiq Khan",
        # World Leaders
        "Vladimir Putin", "Volodymyr Zelenskyy", "Emmanuel Macron", "Angela Merkel", "Justin Trudeau",
        "Xi Jinping", "Narendra Modi", "Jair Bolsonaro", "Benjamin Netanyahu", "Kim Jong-un",
        # Activists & Influencers
        "Greta Thunberg", "Malala Yousafzai", "Andrew Tate", "Jordan Peterson", "Joe Rogan",
        "Ben Shapiro", "Tucker Carlson", "Piers Morgan", "Megyn Kelly", "Rachel Maddow",
        # Business & Other
        "Richard Branson", "Alan Sugar", "Warren Buffett", "Oprah Winfrey", "Martha Stewart",
        "Pope Francis", "Dalai Lama", "Neil deGrasse Tyson", "Bill Nye", "Dr Phil"
    ],
    "tv_personalities": [
        # UK TV Presenters
        "Graham Norton", "Jonathan Ross", "Alan Carr", "James Corden", "Piers Morgan",
        "Holly Willoughby", "Phillip Schofield", "Ant McPartlin", "Dec Donnelly", "Dermot O'Leary",
        "Claudia Winkleman", "Tess Daly", "Rylan Clark", "Alison Hammond", "Rochelle Humes",
        "Vernon Kay", "Lorraine Kelly", "Susanna Reid", "Kate Garraway", "Ben Shephard",
        "Davina McCall", "Emma Willis", "Paddy McGuinness", "Keith Lemon", "Fearne Cotton",
        "Christine Lampard", "Ruth Langsford", "Eamonn Holmes", "Nadia Sawalha", "Coleen Nolan",
        # Entertainment Show Hosts
        "Simon Cowell", "Amanda Holden", "David Walliams", "Alesha Dixon", "Bruno Tonioli",
        "Craig Revel Horwood", "Shirley Ballas", "Motsi Mabuse", "Anton Du Beke", "Oti Mabuse",
        # Sports Presenters
        "Gary Lineker", "Ian Wright", "Alan Shearer", "Gabby Logan", "Clare Balding",
        "Alex Scott", "Micah Richards", "Rio Ferdinand", "Jamie Carragher", "Gary Neville",
        # Science/Documentary Presenters
        "David Attenborough", "Brian Cox", "Stephen Fry", "Michael Palin",
        # US TV Personalities
        "Oprah Winfrey", "Ellen DeGeneres", "Jimmy Fallon", "Jimmy Kimmel", "Stephen Colbert",
        "Trevor Noah", "James Corden", "Ryan Seacrest", "Carson Daly", "Kelly Clarkson"
    ],
    "other": [
        # Chefs
        "Gordon Ramsay", "Jamie Oliver", "Nigella Lawson", "Mary Berry", "Paul Hollywood",
        "Prue Leith", "Ainsley Harriott", "Gino D'Acampo", "James Martin", "Nadiya Hussain",
        # Comedians
        "Peter Kay", "Michael McIntyre", "Ricky Gervais", "Jimmy Carr", "Russell Howard",
        "Jack Whitehall", "Rob Beckett", "Romesh Ranganathan", "Kevin Hart", "Chris Rock",
        "Dave Chappelle", "Joe Rogan", "Russell Brand", "Eddie Izzard", "Sarah Millican",
        # Adventurers/Explorers
        "Bear Grylls", "Jeremy Clarkson", "Richard Hammond", "James May", "Ranulph Fiennes",
        # Beckham Family
        "David Beckham", "Victoria Beckham", "Brooklyn Beckham", "Romeo Beckham", "Cruz Beckham",
        # Models & Influencers  
        "Naomi Campbell", "Kate Moss", "Cara Delevingne", "Rosie Huntington-Whiteley", "Daisy Lowe",
        "Zoe Sugg", "Tanya Burr", "Mrs Hinch", "Stacey Solomon", "Joe Wicks",
        # Writers/Authors
        "J.K. Rowling", "Stephen King", "George R.R. Martin", "Neil Gaiman", "Dan Brown",
        # Business/Entrepreneurs (non-political)
        "Richard Branson", "Alan Sugar", "Deborah Meaden", "Peter Jones", "Theo Paphitis",
        # Other
        "Chris Hughes"
    ]
}

# HOT CELEBS POOL - Large pool to randomly select from on each refresh
HOT_CELEBS_POOL = [
    # Royals
    {"name": "Prince Andrew", "reason": "Royal scandal & legal battles", "tier": "A", "category": "royals"},
    {"name": "Meghan Markle", "reason": "Netflix & Royal drama", "tier": "A", "category": "royals"},
    {"name": "Prince Harry", "reason": "Spare memoir revelations", "tier": "A", "category": "royals"},
    {"name": "Kate Middleton", "reason": "Royal duties & fashion", "tier": "A", "category": "royals"},
    {"name": "King Charles III", "reason": "Royal family head", "tier": "A", "category": "royals"},
    # Musicians
    {"name": "Kanye West", "reason": "Controversy & headlines", "tier": "A", "category": "musicians"},
    {"name": "Taylor Swift", "reason": "Eras Tour & awards", "tier": "A", "category": "musicians"},
    {"name": "Beyoncé", "reason": "Renaissance & Grammys", "tier": "A", "category": "musicians"},
    {"name": "Drake", "reason": "Music & feuds", "tier": "A", "category": "musicians"},
    {"name": "Rihanna", "reason": "Fenty & fashion empire", "tier": "A", "category": "musicians"},
    {"name": "Ed Sheeran", "reason": "Tours & legal battles", "tier": "A", "category": "musicians"},
    {"name": "Adele", "reason": "Vegas residency", "tier": "A", "category": "musicians"},
    {"name": "Bad Bunny", "reason": "Latin music & film debut", "tier": "C", "category": "musicians"},
    {"name": "Britney Spears", "reason": "Memoir & documentaries", "tier": "B", "category": "musicians"},
    {"name": "Barry Manilow", "reason": "Vegas & health news", "tier": "C", "category": "musicians"},
    # Tech/Business
    {"name": "Elon Musk", "reason": "Tech & politics headlines", "tier": "A", "category": "other"},
    {"name": "Mark Zuckerberg", "reason": "Meta & AI news", "tier": "A", "category": "other"},
    {"name": "Jeff Bezos", "reason": "Space & business", "tier": "A", "category": "other"},
    # Politicians
    {"name": "Donald Trump", "reason": "Political & legal news", "tier": "A", "category": "other"},
    {"name": "Joe Biden", "reason": "Political headlines", "tier": "A", "category": "other"},
    # Reality TV/UK
    {"name": "Katie Price", "reason": "Tabloid regular", "tier": "D", "category": "reality_tv"},
    {"name": "Holly Willoughby", "reason": "TV drama", "tier": "D", "category": "tv_actors"},
    {"name": "Phillip Schofield", "reason": "TV scandal", "tier": "D", "category": "tv_actors"},
    {"name": "Gemma Collins", "reason": "Reality star antics", "tier": "D", "category": "reality_tv"},
    {"name": "Kerry Katona", "reason": "Tabloid stories", "tier": "D", "category": "reality_tv"},
    {"name": "Simone Biles", "reason": "Olympic champion", "tier": "D", "category": "athletes"},
    # Actors
    {"name": "Tom Cruise", "reason": "Mission Impossible & stunts", "tier": "A", "category": "movie_stars"},
    {"name": "Leonardo DiCaprio", "reason": "Film & dating life", "tier": "A", "category": "movie_stars"},
    {"name": "Jennifer Lawrence", "reason": "Film & fashion", "tier": "A", "category": "movie_stars"},
    {"name": "Brad Pitt", "reason": "Films & personal life", "tier": "A", "category": "movie_stars"},
    {"name": "Angelina Jolie", "reason": "Humanitarian & acting", "tier": "A", "category": "movie_stars"},
    {"name": "Eric Dane", "reason": "Grey's Anatomy star", "tier": "D", "category": "tv_actors"},
    {"name": "Shia LaBeouf", "reason": "Film & controversy", "tier": "B", "category": "movie_stars"},
    {"name": "Margot Robbie", "reason": "Barbie & film roles", "tier": "A", "category": "movie_stars"},
    # Sports
    {"name": "Cristiano Ronaldo", "reason": "Football & brand deals", "tier": "A", "category": "athletes"},
    {"name": "David Beckham", "reason": "Business & family", "tier": "A", "category": "athletes"},
    {"name": "Lewis Hamilton", "reason": "F1 & fashion", "tier": "A", "category": "athletes"},
    # NEW - Hot due to recent news coverage
    {"name": "Timothée Chalamet", "reason": "Dune sequel & awards buzz", "tier": "A", "category": "movie_stars"},
    {"name": "Zendaya", "reason": "Challengers film & fashion icon", "tier": "A", "category": "movie_stars"},
    {"name": "Travis Kelce", "reason": "NFL star & Taylor Swift relationship", "tier": "B", "category": "athletes"},
    {"name": "Sydney Sweeney", "reason": "Euphoria star & film roles", "tier": "B", "category": "tv_actors"},
]

def get_random_hot_celebs(count: int = 8) -> list:
    """Get a random selection of hot celebs from the pool"""
    # Ensure we have a good mix of tiers
    a_list = [c for c in HOT_CELEBS_POOL if c["tier"] == "A"]
    b_list = [c for c in HOT_CELEBS_POOL if c["tier"] in ["B", "C"]]
    
    # Pick mostly A-list with some B/C list
    selected = random.sample(a_list, min(6, len(a_list)))
    if b_list:
        selected += random.sample(b_list, min(2, len(b_list)))
    
    random.shuffle(selected)
    return selected[:count]

# A-list indicators (keywords that suggest high fame)
A_LIST_INDICATORS = ["oscar", "grammy", "emmy", "golden globe", "bafta", "world cup winner", 
                      "billion", "legendary", "iconic", "superstar", "megastar", "one of the most",
                      "best-selling", "highest-paid", "most famous", "world record"]
B_LIST_INDICATORS = ["award-winning", "acclaimed", "successful", "popular", "well-known", 
                      "million", "chart-topping", "hit", "starring", "lead role"]
C_LIST_INDICATORS = ["known for", "appeared in", "featured", "contestant", "participant"]

# Mega-stars who should ALWAYS be A-list regardless of bio analysis
GUARANTEED_A_LIST = [
    "taylor swift", "beyoncé", "beyonce", "rihanna", "drake", "kanye west", "adele",
    "ed sheeran", "ariana grande", "justin bieber", "lady gaga", "bruno mars",
    "leonardo dicaprio", "tom cruise", "brad pitt", "angelina jolie", "tom hanks",
    "julia roberts", "denzel washington", "will smith", "johnny depp", "robert downey jr",
    "dwayne johnson", "the rock", "scarlett johansson", "jennifer lawrence", "margot robbie",
    "oprah winfrey", "kim kardashian", "elon musk", "jeff bezos", "cristiano ronaldo",
    "lionel messi", "lebron james", "serena williams", "roger federer", "michael jordan",
    "david beckham", "barack obama", "donald trump", "joe biden", "bill gates",
    # British Royal Family (all variations including Wikipedia formal names)
    "prince william", "william, prince of wales", "william prince of wales",
    "prince harry", "harry, duke of sussex", "harry duke of sussex", "prince harry, duke of sussex", "prince harry duke of sussex",
    "kate middleton", "catherine, princess of wales", "catherine princess of wales",
    "queen elizabeth", "elizabeth ii", "queen elizabeth ii",
    "king charles", "charles iii", "king charles iii",
    "prince andrew", "andrew, duke of york", "andrew duke of york", "andrew mountbatten-windsor",
    "meghan markle", "meghan, duchess of sussex", "meghan duchess of sussex",
    "princess diana", "diana, princess of wales", "diana princess of wales",
    "camilla", "queen camilla", "camilla, queen consort",
    "princess anne", "anne, princess royal", "anne princess royal",
    "prince edward", "edward, duke of edinburgh", "edward duke of edinburgh",
    "princess beatrice", "princess eugenie", "zara tindall", "peter phillips",
    # Royal Children - Prince William's children
    "prince george", "prince george of wales", "george of wales",
    "princess charlotte", "princess charlotte of wales", "charlotte of wales",
    "prince louis", "prince louis of wales", "louis of wales",
    # Royal Children - Prince Harry's children
    "prince archie", "prince archie of sussex", "archie of sussex", "archie harrison",
    "princess lilibet", "princess lilibet of sussex", "lilibet of sussex", "lilibet diana",
    "prince george", "princess charlotte", "prince louis",
    # Additional mega-stars
    "britney spears", "madonna", "michael jackson", "jennifer lopez", "shakira",
    "eminem", "jay-z", "jay z", "snoop dogg", "50 cent", "nicki minaj", "cardi b",
    "selena gomez", "miley cyrus", "katy perry", "demi lovato", "the weeknd",
    "tom brady", "tiger woods", "usain bolt", "muhammad ali", "mike tyson",
    "meryl streep", "nicole kidman", "cate blanchett", "natalie portman", "emma watson",
    "george clooney", "matt damon", "ben affleck", "keanu reeves", "morgan freeman",
    "samuel l. jackson", "samuel l jackson", "al pacino", "robert de niro", "jack nicholson",
    # Sports legends
    "simone biles", "venus williams", "novak djokovic", "wayne rooney", "diego maradona",
    "pele", "pelé", "zinedine zidane", "kobe bryant", "shaquille o'neal"
]

# Keywords that indicate A-list royalty (for partial matching)
ROYAL_A_LIST_KEYWORDS = ["prince william", "prince harry", "king charles", "kate middleton", 
                          "meghan markle", "princess diana", "queen elizabeth", "prince andrew",
                          "princess anne", "prince edward", "duke of sussex", "duke of york",
                          "prince of wales", "princess of wales", "duke of edinburgh"]

# Celebrity name aliases - maps alternate names to canonical Wikipedia names
# This prevents users from adding the same person twice under different names
CELEBRITY_ALIASES = {
    # British Royals
    "prince william": "William, Prince of Wales",
    "william": "William, Prince of Wales",
    "prince harry": "Prince Harry, Duke of Sussex",
    "harry": "Prince Harry, Duke of Sussex",
    "kate middleton": "Catherine, Princess of Wales",
    "princess kate": "Catherine, Princess of Wales",
    "catherine middleton": "Catherine, Princess of Wales",
    "king charles": "Charles III",
    "prince charles": "Charles III",
    "king charles iii": "Charles III",
    "prince andrew": "Prince Andrew, Duke of York",
    "andrew mountbatten-windsor": "Prince Andrew, Duke of York",
    "meghan markle": "Meghan, Duchess of Sussex",
    "duchess of sussex": "Meghan, Duchess of Sussex",
    "queen elizabeth": "Elizabeth II",
    "queen elizabeth ii": "Elizabeth II",
    "princess diana": "Diana, Princess of Wales",
    "lady diana": "Diana, Princess of Wales",
    "camilla": "Queen Camilla",
    "queen camilla": "Queen Camilla",
    # Other celebs with common alternate names
    "the rock": "Dwayne Johnson",
    "dwayne 'the rock' johnson": "Dwayne Johnson",
    "jay z": "Jay-Z",
    "jay-z": "Jay-Z",
    "50 cent": "50 Cent",
    "fiddy": "50 Cent",
    "p diddy": "Sean Combs",
    "puff daddy": "Sean Combs",
    "diddy": "Sean Combs",
    "snoop dogg": "Snoop Dogg",
    "snoop dog": "Snoop Dogg",
    "lady gaga": "Lady Gaga",
    "stefani germanotta": "Lady Gaga",
    # Brian Cox disambiguation
    "brian cox": "Brian Cox (physicist)",
    "brian cox physicist": "Brian Cox (physicist)",
    "brian cox scientist": "Brian Cox (physicist)",
    "professor brian cox": "Brian Cox (physicist)",
    "brian cox actor": "Brian Cox (actor)",
    # Reality TV Personalities
    "sam thompson": "Sam Thompson (TV personality)",
    "spencer matthews": "Spencer Matthews",
    # Musicians with disambiguation
    "drake": "Drake (musician)",
    "usher": "Usher (musician)",
    "chris brown": "Chris Brown",
    # Sports presenters
    "alex scott": "Alex Scott (footballer, born 1984)",
    "george russell": "George Russell (racing driver)",
    # Royals with disambiguation
    "prince edward": "Prince Edward, Duke of Edinburgh",
    "prince frederick": "Frederik X",
    "prince frederik of denmark": "Frederik X",
    "sophie duchess of edinburgh": "Sophie, Duchess of Edinburgh",
    "sophie wessex": "Sophie, Duchess of Edinburgh",
    "james viscount severn": "James, Earl of Wessex",
    "king willem-alexander": "Willem-Alexander of the Netherlands",
    "king willem-alexander of netherlands": "Willem-Alexander of the Netherlands",
    "queen maxima": "Queen Máxima of the Netherlands",
    "queen maxima of netherlands": "Queen Máxima of the Netherlands",
    # Royal Children - Prince William's kids
    "prince george": "Prince George of Wales",
    "george cambridge": "Prince George of Wales",
    "george of wales": "Prince George of Wales",
    "princess charlotte": "Princess Charlotte of Wales",
    "charlotte cambridge": "Princess Charlotte of Wales",
    "charlotte of wales": "Princess Charlotte of Wales",
    "prince louis": "Prince Louis of Wales",
    "louis cambridge": "Princess Louis of Wales",
    "louis of wales": "Prince Louis of Wales",
    # Royal Children - Prince Harry's kids
    "prince archie": "Prince Archie of Sussex",
    "archie mountbatten-windsor": "Prince Archie of Sussex",
    "archie of sussex": "Prince Archie of Sussex",
    "archie harrison": "Prince Archie of Sussex",
    "princess lilibet": "Princess Lilibet of Sussex",
    "lilibet mountbatten-windsor": "Princess Lilibet of Sussex", 
    "lilibet of sussex": "Princess Lilibet of Sussex",
    "lilibet diana": "Princess Lilibet of Sussex",
    # Actors with disambiguation
    "christopher evans": "Chris Evans",
    "chris evans actor": "Chris Evans",
    "chris evans captain america": "Chris Evans",
}

# Reverse mapping - canonical name to all aliases (for duplicate checking)
def get_all_name_variants(canonical_name: str) -> set:
    """Get all name variants for a canonical celebrity name"""
    variants = {canonical_name.lower()}
    for alias, canonical in CELEBRITY_ALIASES.items():
        if canonical.lower() == canonical_name.lower():
            variants.add(alias.lower())
    return variants

def get_canonical_name(name: str) -> str:
    """Get the canonical name for a celebrity (or return original if no alias)"""
    return CELEBRITY_ALIASES.get(name.lower(), name)

def are_same_celebrity(name1: str, name2: str) -> bool:
    """Check if two names refer to the same celebrity"""
    canonical1 = get_canonical_name(name1).lower()
    canonical2 = get_canonical_name(name2).lower()
    return canonical1 == canonical2

# Guaranteed B-list celebrities (not quite A-list but definitely not C or D)
GUARANTEED_B_LIST = [
    "shia labeouf", "megan fox", "lindsay lohan", "paris hilton", "nicole richie",
    "pete davidson", "machine gun kelly", "mgk", "post malone", "travis scott",
    "kylie jenner", "kendall jenner", "khloe kardashian", "kourtney kardashian",
    "gigi hadid", "bella hadid", "cara delevingne", "emily ratajkowski",
    "zac efron", "channing tatum", "ryan reynolds", "chris pratt", "chris evans",
    "henry cavill", "jason momoa", "idris elba", "tom hardy", "benedict cumberbatch"
]

# Guaranteed C-list celebrities (TV personalities, chefs, etc.)
GUARANTEED_C_LIST = [
    "gordon ramsay", "jamie oliver", "simon cowell", "piers morgan", "james corden",
    "jimmy fallon", "jimmy kimmel", "ellen degeneres", "graham norton", "alan carr",
    "rylan clark", "phillip schofield", "holly willoughby", "amanda holden",
    "ant mcpartlin", "declan donnelly", "dermot o'leary", "davina mccall"
]


#!/usr/bin/env python3
"""Script to populate database with 200 celebrities per category"""
import asyncio
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from datetime import datetime, timezone

# Extended celebrity lists - 200+ per category
EXTENDED_POOLS = {
    "movie_stars": [
        # Current A-listers
        "Tom Holland", "Florence Pugh", "Idris Elba", "Emily Blunt", "Dev Patel",
        "Leonardo DiCaprio", "Brad Pitt", "Angelina Jolie", "Tom Cruise", "Jennifer Lawrence",
        "Margot Robbie", "Ryan Gosling", "Emma Stone", "Chris Hemsworth", "Scarlett Johansson",
        "Robert Downey Jr", "Chris Evans", "Zendaya", "Timothee Chalamet", "Sydney Sweeney",
        "Ana de Armas", "Austin Butler", "Jacob Elordi", "Glen Powell", "Jenna Ortega",
        "Anya Taylor-Joy", "Paul Mescal", "Barry Keoghan", "Daisy Edgar-Jones", "Josh O'Connor",
        "Cillian Murphy", "Dakota Johnson", "Pedro Pascal", "Oscar Isaac", "Jason Momoa",
        "Gal Gadot", "Henry Cavill", "Dwayne Johnson", "Vin Diesel", "Keanu Reeves",
        "Sandra Bullock", "Julia Roberts", "George Clooney", "Matt Damon", "Ben Affleck",
        "Jennifer Garner", "Reese Witherspoon", "Nicole Kidman", "Cate Blanchett", "Meryl Streep",
        "Viola Davis", "Denzel Washington", "Samuel L Jackson", "Morgan Freeman", "Al Pacino",
        "Robert De Niro", "Michael Caine", "Anthony Hopkins", "Ian McKellen", "Patrick Stewart",
        "Judi Dench", "Helen Mirren", "Emma Thompson", "Kate Winslet", "Rachel McAdams",
        "Anne Hathaway", "Natalie Portman", "Keira Knightley", "Saoirse Ronan", "Chris Pratt",
        "Ryan Reynolds", "Hugh Jackman", "Mark Wahlberg", "Will Smith", "Johnny Depp",
        "Tom Hanks", "Harrison Ford", "Michael B Jordan", "John Boyega", "Lupita Nyongo",
        "Awkwafina", "Simu Liu", "Gemma Chan", "Michelle Yeoh", "Jamie Lee Curtis",
        "Brendan Fraser", "Ke Huy Quan", "Jessica Chastain", "Julianne Moore", "Amy Adams",
        "Hailee Steinfeld", "Elle Fanning", "Dakota Fanning", "Shailene Woodley", "Brie Larson",
        "Tessa Thompson", "Letitia Wright", "Danai Gurira", "Elizabeth Olsen", "Paul Rudd",
        "Don Cheadle", "Mark Ruffalo", "Jeremy Renner", "Benedict Cumberbatch", "Tom Hiddleston",
        "Idris Elba", "Chiwetel Ejiofor", "Daniel Kaluuya", "Lakeith Stanfield", "LaKeith Stanfield",
        "John David Washington", "Yahya Abdul-Mateen II", "Jonathan Majors", "Keke Palmer",
        "Regina King", "Octavia Spencer", "Taraji P Henson", "Angela Bassett", "Halle Berry",
        "Salma Hayek", "Penelope Cruz", "Javier Bardem", "Antonio Banderas", "Sofia Vergara",
        "Eugenio Derbez", "Diego Luna", "Gael Garcia Bernal", "Oscar Isaac", "Pedro Pascal",
        "Lin-Manuel Miranda", "John Leguizamo", "America Ferrera", "Eva Longoria", "Zoe Saldana",
        "Rosario Dawson", "Michelle Rodriguez", "Jennifer Lopez", "Cameron Diaz", "Drew Barrymore",
        "Adam Sandler", "Ben Stiller", "Owen Wilson", "Vince Vaughn", "Will Ferrell",
        "Steve Carell", "Paul Rudd", "Seth Rogen", "Jonah Hill", "James Franco",
        "Jake Gyllenhaal", "Tobey Maguire", "Kirsten Dunst", "James McAvoy", "Michael Fassbender",
        "Jennifer Lawrence", "Josh Hutcherson", "Liam Hemsworth", "Sam Claflin", "Stanley Tucci",
        "Woody Harrelson", "Donald Sutherland", "Philip Seymour Hoffman", "Julianne Moore",
        "Jeff Bridges", "Colin Firth", "Geoffrey Rush", "Christian Bale", "Gary Oldman",
        "Eddie Redmayne", "Andrew Garfield", "Jesse Eisenberg", "Miles Teller", "Ansel Elgort",
        "Lily James", "Alicia Vikander", "Felicity Jones", "Rosamund Pike", "Ruth Negga",
        "Carey Mulligan", "Rooney Mara", "Kate Mara", "Emily Mortimer", "Romola Garai"
    ],
    "tv_actors": [
        "Jenna Coleman", "Jodie Comer", "Richard Madden", "Ncuti Gatwa", "Olivia Colman",
        "David Tennant", "Matt Smith", "Peter Capaldi", "Jodie Whittaker", "Karen Gillan",
        "Suranne Jones", "Martin Compston", "Vicky McClure", "Adrian Dunbar", "Keeley Hawes",
        "Ruth Wilson", "Dominic West", "Gillian Anderson", "Jamie Dornan", "Cush Jumbo",
        "David Oyelowo", "Thandiwe Newton", "Michaela Coel", "Phoebe Waller-Bridge", "Andrew Scott",
        "Rosamund Pike", "Maxine Peake", "Sheridan Smith", "Sarah Lancashire", "Stephen Graham",
        "Sean Bean", "Gemma Arterton", "Naomie Harris", "Kit Harington", "Emilia Clarke",
        "Sophie Turner", "Maisie Williams", "Nikolaj Coster-Waldau", "Bryan Cranston", "Aaron Paul",
        "Elisabeth Moss", "Steve Carell", "Jenna Fischer", "Rainn Wilson", "John Krasinski",
        "Sarah Snook", "Jeremy Strong", "Matthew Macfadyen", "Kieran Culkin", "Jason Sudeikis",
        "Hannah Waddingham", "Brett Goldstein", "Zooey Deschanel", "Kaley Cuoco", "Jim Parsons",
        "Johnny Galecki", "Kunal Nayyar", "Jennifer Aniston", "Courteney Cox", "Lisa Kudrow",
        "Matt LeBlanc", "David Schwimmer", "Sofia Vergara", "Julie Bowen", "Ty Burrell",
        "Jesse Tyler Ferguson", "Eric Stonestreet", "Zach Braff", "Donald Faison", "Neil Patrick Harris",
        "Jason Segel", "Alyson Hannigan", "Cobie Smulders", "Josh Radnor", "Cristin Milioti",
        "Bob Odenkirk", "Rhea Seehorn", "Michael Mando", "Jonathan Banks", "Giancarlo Esposito",
        "Sterling K Brown", "Mandy Moore", "Milo Ventimiglia", "Chrissy Metz", "Justin Hartley",
        "Millie Bobby Brown", "Finn Wolfhard", "Gaten Matarazzo", "Caleb McLaughlin", "Noah Schnapp",
        "Sadie Sink", "Winona Ryder", "David Harbour", "Natalia Dyer", "Charlie Heaton",
        "Pedro Pascal", "Bella Ramsey", "Nick Offerman", "Murray Bartlett", "Anna Torv",
        "Evan Peters", "Sarah Paulson", "Lily Rabe", "Angela Bassett", "Emma Roberts",
        "Jessica Lange", "Kathy Bates", "Denis OHare", "Cody Fern", "Billy Porter",
        "Sandra Oh", "Jodie Comer", "Fiona Shaw", "Kim Bodnia", "Camille Cottin",
        "Damson Idris", "Emily Rios", "Carter Hudson", "Angela Lewis", "Amin Joseph",
        "Viola Davis", "Billy Brown", "Liza Weil", "Matt McGorry", "Jack Falahee",
        "Aja Naomi King", "Karla Souza", "Charlie Weber", "Conrad Ricamora", "Alfred Enoch",
        "Kerry Washington", "Tony Goldwyn", "Scott Foley", "Bellamy Young", "Jeff Perry",
        "Darby Stanchfield", "Katie Lowes", "Guillermo Diaz", "Josh Malina", "Portia de Rossi"
    ],
    "musicians": [
        "Dua Lipa", "Ed Sheeran", "Adele", "Harry Styles", "Stormzy",
        "Taylor Swift", "Beyonce", "Rihanna", "Lady Gaga", "Ariana Grande",
        "Billie Eilish", "Olivia Rodrigo", "Doja Cat", "SZA", "Lizzo",
        "Post Malone", "Bad Bunny", "Kendrick Lamar", "Travis Scott", "The Weeknd",
        "Bruno Mars", "Justin Bieber", "Shawn Mendes", "Charlie Puth", "Sam Smith",
        "Lewis Capaldi", "Tom Grennan", "George Ezra", "Rag n Bone Man", "Elton John",
        "Paul McCartney", "Mick Jagger", "Rod Stewart", "Ozzy Osbourne", "Noel Gallagher",
        "Liam Gallagher", "Robbie Williams", "Gary Barlow", "Olly Murs", "Rita Ora",
        "Jessie J", "Anne-Marie", "Ellie Goulding", "Florence Welch", "Leona Lewis",
        "Cheryl Cole", "Nicole Scherzinger", "Mel B", "Cardi B", "Megan Thee Stallion",
        "Nicki Minaj", "Ice Spice", "Latto", "Miley Cyrus", "Selena Gomez",
        "Demi Lovato", "Katy Perry", "Pink", "Justin Timberlake", "Usher",
        "Chris Brown", "Jason Derulo", "Ne-Yo", "John Legend", "Alicia Keys",
        "Mary J Blige", "Janet Jackson", "Mariah Carey", "Celine Dion", "Whitney Houston",
        "Madonna", "Cher", "Barbra Streisand", "Diana Ross", "Stevie Wonder",
        "Michael Buble", "Josh Groban", "Andrea Bocelli", "Il Divo", "Josh Turner",
        "Carrie Underwood", "Blake Shelton", "Luke Bryan", "Jason Aldean", "Keith Urban",
        "Tim McGraw", "Faith Hill", "Reba McEntire", "Dolly Parton", "Willie Nelson",
        "Johnny Cash", "Elvis Presley", "Frank Sinatra", "Nat King Cole", "Dean Martin",
        "Tony Bennett", "Harry Connick Jr", "Diana Krall", "Norah Jones", "Amy Winehouse",
        "Duffy", "Joss Stone", "Corinne Bailey Rae", "Seal", "Sade",
        "Craig David", "James Arthur", "Cher Lloyd", "Little Mix", "One Direction",
        "JLS", "The Wanted", "McFly", "Busted", "Blue", "Westlife", "Take That",
        "Spice Girls", "Girls Aloud", "Sugababes", "All Saints", "Atomic Kitten",
        "Steps", "S Club 7", "Hear Say", "Pop Idol", "X Factor",
        "Coldplay", "Arctic Monkeys", "The 1975", "Bastille", "Mumford and Sons",
        "Florence and the Machine", "Gorillaz", "Blur", "Oasis", "Pulp",
        "Radiohead", "Muse", "Snow Patrol", "Keane", "The Killers",
        "Foo Fighters", "Green Day", "Blink-182", "Fall Out Boy", "Panic at the Disco",
        "My Chemical Romance", "Paramore", "Twenty One Pilots", "Imagine Dragons", "OneRepublic",
        "Maroon 5", "Coldplay", "U2", "Bon Jovi", "Aerosmith",
        "Queen", "Led Zeppelin", "Pink Floyd", "The Rolling Stones", "The Beatles"
    ],
    "athletes": [
        "Harry Kane", "Marcus Rashford", "Emma Raducanu", "Lewis Hamilton", "Raheem Sterling",
        "Bukayo Saka", "Phil Foden", "Jude Bellingham", "Declan Rice", "Jack Grealish",
        "Mason Mount", "Jadon Sancho", "Trent Alexander-Arnold", "Jordan Henderson", "Kyle Walker",
        "John Stones", "Kalvin Phillips", "Jordan Pickford", "Aaron Ramsdale", "Ben White",
        "Reece James", "Ben Chilwell", "James Maddison", "Ivan Toney", "Ollie Watkins",
        "Eberechi Eze", "Cole Palmer", "Anthony Gordon", "Jarrod Bowen", "Conor Gallagher",
        "Mohamed Salah", "Kevin De Bruyne", "Erling Haaland", "Bruno Fernandes", "Virgil van Dijk",
        "Martin Odegaard", "Son Heung-min", "James Ward-Prowse", "Kieran Trippier", "Callum Wilson",
        "Dominic Calvert-Lewin", "Danny Ings", "Jamie Vardy", "Wilfried Zaha", "Michael Olise",
        "Andy Murray", "Emma Raducanu", "Cameron Norrie", "Dan Evans", "Jack Draper",
        "Katie Boulter", "Harriet Dart", "Johanna Konta", "Heather Watson", "Laura Robson",
        "Lewis Hamilton", "George Russell", "Lando Norris", "Max Verstappen", "Charles Leclerc",
        "Carlos Sainz", "Fernando Alonso", "Sebastian Vettel", "Jenson Button", "David Coulthard",
        "Damon Hill", "Nigel Mansell", "Jackie Stewart", "Stirling Moss", "Graham Hill",
        "Anthony Joshua", "Tyson Fury", "Amir Khan", "Carl Froch", "Lennox Lewis",
        "Ricky Hatton", "Joe Calzaghe", "Chris Eubank", "Nigel Benn", "Frank Bruno",
        "Tom Daley", "Adam Peaty", "Duncan Scott", "James Guy", "Rebecca Adlington",
        "Laura Kenny", "Jason Kenny", "Chris Hoy", "Victoria Pendleton", "Bradley Wiggins",
        "Mark Cavendish", "Chris Froome", "Geraint Thomas", "Adam Yates", "Simon Yates",
        "Jessica Ennis-Hill", "Mo Farah", "Dina Asher-Smith", "Katarina Johnson-Thompson", "Greg Rutherford",
        "Paula Radcliffe", "Kelly Holmes", "Denise Lewis", "Daley Thompson", "Seb Coe",
        "Steve Ovett", "Steve Cram", "Brendan Foster", "David Bedford", "Roger Bannister",
        "Rory McIlroy", "Tommy Fleetwood", "Justin Rose", "Ian Poulter", "Lee Westwood",
        "Luke Donald", "Paul Casey", "Danny Willett", "Tyrrell Hatton", "Matt Fitzpatrick",
        "Nick Faldo", "Colin Montgomerie", "Sandy Lyle", "Tony Jacklin", "Seve Ballesteros",
        "Tiger Woods", "Phil Mickelson", "Dustin Johnson", "Brooks Koepka", "Jordan Spieth",
        "Johnny Wilkinson", "Owen Farrell", "Maro Itoje", "George Ford", "Billy Vunipola",
        "Ben Youngs", "Manu Tuilagi", "Courtney Lawes", "Tom Curry", "Sam Underhill",
        "Alun Wyn Jones", "Dan Biggar", "Jonathan Davies", "Liam Williams", "Josh Adams",
        "Stuart Hogg", "Finn Russell", "Hamish Watson", "Rory Sutherland", "Jonny Gray",
        "Serena Williams", "Venus Williams", "Naomi Osaka", "Coco Gauff", "Iga Swiatek",
        "Novak Djokovic", "Rafael Nadal", "Roger Federer", "Carlos Alcaraz", "Daniil Medvedev",
        "LeBron James", "Stephen Curry", "Kevin Durant", "Giannis Antetokounmpo", "Luka Doncic",
        "Tom Brady", "Patrick Mahomes", "Aaron Rodgers", "Josh Allen", "Lamar Jackson",
        "Lionel Messi", "Cristiano Ronaldo", "Neymar", "Kylian Mbappe", "Robert Lewandowski"
    ],
    "royals": [
        "King Charles III", "Queen Camilla", "Prince William", "Catherine Princess of Wales",
        "Prince George of Wales", "Princess Charlotte of Wales", "Prince Louis of Wales",
        "Prince Harry", "Meghan Markle", "Prince Archie of Sussex", "Princess Lilibet of Sussex",
        "Princess Anne", "Peter Phillips", "Zara Tindall", "Mike Tindall",
        "Savannah Phillips", "Isla Phillips", "Mia Tindall", "Lena Tindall", "Lucas Tindall",
        "Prince Andrew", "Princess Beatrice", "Edoardo Mapelli Mozzi", "Sienna Mapelli Mozzi",
        "Princess Eugenie", "Jack Brooksbank", "August Brooksbank", "Ernest Brooksbank",
        "Prince Edward Duke of Edinburgh", "Sophie Duchess of Edinburgh", "Lady Louise Windsor", "James Earl of Wessex",
        "Sarah Ferguson", "Lady Kitty Spencer", "Lady Eliza Spencer", "Lady Amelia Spencer",
        "Louis Spencer Viscount Althorp", "Earl Spencer", "Princess Diana",
        "Queen Elizabeth II", "Prince Philip", "Queen Mother", "Princess Margaret",
        "Lady Sarah Chatto", "Samuel Chatto", "Arthur Chatto", "David Armstrong-Jones",
        "Prince Michael of Kent", "Princess Michael of Kent", "Lord Frederick Windsor", "Lady Gabriella Kingston",
        "Prince Richard Duke of Gloucester", "Birgitte Duchess of Gloucester",
        "Prince Edward Duke of Kent", "Katharine Duchess of Kent", "Lady Helen Taylor",
        "Frederik X", "Queen Mary of Denmark", "Prince Christian of Denmark",
        "Princess Isabella of Denmark", "Prince Vincent of Denmark", "Princess Josephine of Denmark",
        "Willem-Alexander of the Netherlands", "Queen Maxima of the Netherlands",
        "Princess Catharina-Amalia", "Princess Alexia of the Netherlands", "Princess Ariane",
        "King Felipe VI", "Queen Letizia", "Princess Leonor", "Infanta Sofia",
        "King Carl XVI Gustaf", "Queen Silvia of Sweden", "Crown Princess Victoria",
        "Prince Daniel", "Princess Estelle", "Prince Oscar", "Prince Carl Philip",
        "Princess Sofia of Sweden", "Princess Madeleine", "Harald V of Norway",
        "Queen Sonja of Norway", "Crown Prince Haakon", "Crown Princess Mette-Marit",
        "Princess Ingrid Alexandra", "Prince Sverre Magnus", "Princess Martha Louise",
        "King Philippe of Belgium", "Queen Mathilde", "Princess Elisabeth Duchess of Brabant",
        "Prince Gabriel of Belgium", "Prince Emmanuel of Belgium", "Princess Eleonore of Belgium",
        "Albert II Prince of Monaco", "Charlene Princess of Monaco", "Prince Jacques",
        "Princess Gabriella", "Pierre Casiraghi", "Andrea Casiraghi", "Charlotte Casiraghi",
        "Grand Duke Henri", "Grand Duchess Maria Teresa", "Prince Guillaume",
        "Princess Grace", "Prince Rainier III"
    ],
    "reality_tv": [
        "Katie Price", "Gemma Collins", "Joey Essex", "Tyra Banks", "Kim Kardashian",
        "Kylie Jenner", "Kendall Jenner", "Kourtney Kardashian", "Khloe Kardashian", "Kris Jenner",
        "Spencer Pratt", "Georgia Toffolo", "Spencer Matthews", "Kyle Richards", "Tommy Fury",
        "Paris Hilton", "Louise Thompson", "Holly Hagan", "Amy Childs", "Lisa Vanderpump",
        "Nicole Richie", "Travis Barker", "Michelle Keegan", "Jamie Laing", "Ekin-Su Culculoglu",
        "Scott Disick", "Lucy Watson", "Amber Davies", "Bethenny Frankel", "Zara McDermott",
        "NeNe Leakes", "Lauren Goodger", "Mark Wright", "Olivia Bowen", "Chloe Ferry",
        "Kristin Cavallari", "Brody Jenner", "Kem Cetinay", "Olivia Attwood", "Proudlock",
        "Charlotte Crosby", "Marnie Simpson", "Nathan Massey", "Sam Faiers", "Lauren Conrad",
        "Dani Dyer", "Maura Higgins", "Heidi Montag", "Amber Gill", "Vicky Pattison",
        "Teresa Giudice", "Pete Wicks", "Ollie Locke", "Hailey Bieber", "Billie Shepherd",
        "Chris Hughes", "Molly-Mae Hague", "Paige Turley", "Siannise Fudge", "Luke Trotman",
        "Shaughna Phillips", "Callum Jones", "Nas Majeed", "Eve Gale", "Jess Gale",
        "Demi Jones", "Luke Mabbott", "Natalia Zoppa", "Jamie Clayton", "Priscilla Anyabu",
        "Mike Boateng", "Sophie Piper", "Connagh Howard", "Rebecca Gormley", "Biggs Chris",
        "Shannon Singh", "Chloe Burrows", "Toby Aromolaran", "Faye Winter", "Teddy Soares",
        "Kaz Kamwi", "Tyler Cruickshank", "Millie Court", "Liam Reardon", "Jake Cornish",
        "Liberty Poole", "Hugo Hammond", "Aaron Francis", "Sharon Gaffka", "Lucinda Strafford",
        "Brad McClelland", "Chuggs Wallis", "Danny Bibby", "AJ Bunker", "Georgia Townend",
        "Abigail Rawlings", "Dale Mehmet", "Mary Bedford", "Sam Jackson", "Clarisse Juliette",
        "Matt MacNabb", "Priya Gopaldas", "Brett Staniland", "Tasha Ghouri", "Andrew Le Page",
        "Gemma Owen", "Luca Bish", "Ekin-Su Culculoglu", "Davide Sanclimenti", "Indiyah Polack",
        "Dami Hope", "Paige Thorne", "Adam Collard", "Billy Brown", "Summer Botwe",
        "Josh Le Grove", "Coco Lodge", "Cheyanne Kerr", "George Tasker", "Deji Adeniyi",
        "Reece Ford", "Lacey Edwards", "Nathalia Campos", "Jamie Allen", "Sam Thompson",
        "Made in Chelsea cast", "TOWIE cast", "Geordie Shore cast", "Love Island cast",
        "Real Housewives", "Keeping Up with Kardashians", "The Hills cast", "The Only Way Is Essex",
        "I'm a Celebrity", "Big Brother cast", "Celebrity Big Brother", "Ex on the Beach cast",
        "Bachelor cast", "Bachelorette cast", "Survivor cast", "Amazing Race cast",
        "Dancing with the Stars", "Strictly Come Dancing", "The Voice cast", "X Factor cast"
    ],
    "public_figure": [
        "Elon Musk", "Donald Trump", "Boris Johnson", "Greta Thunberg", "Alexandria Ocasio-Cortez",
        "Joe Rogan", "Andrew Tate", "Jordan Peterson", "Nigel Farage", "Rishi Sunak",
        "Keir Starmer", "Jeremy Corbyn", "Tony Blair", "David Cameron", "Theresa May",
        "Gordon Brown", "John Major", "Margaret Thatcher", "Winston Churchill", "Barack Obama",
        "Joe Biden", "Hillary Clinton", "Bill Clinton", "George W Bush", "Michelle Obama",
        "Melania Trump", "Ivanka Trump", "Jared Kushner", "Donald Trump Jr", "Eric Trump",
        "Nancy Pelosi", "Chuck Schumer", "Mitch McConnell", "Bernie Sanders", "Elizabeth Warren",
        "Pete Buttigieg", "Kamala Harris", "Mike Pence", "Ron DeSantis", "Gavin Newsom",
        "Jeff Bezos", "Bill Gates", "Mark Zuckerberg", "Tim Cook", "Sundar Pichai",
        "Satya Nadella", "Jack Dorsey", "Reed Hastings", "Bob Iger", "Rupert Murdoch",
        "Warren Buffett", "Charlie Munger", "George Soros", "Carl Icahn", "Ken Griffin",
        "Ray Dalio", "Jamie Dimon", "Larry Fink", "Steve Schwarzman", "David Solomon",
        "Richard Branson", "James Dyson", "Alan Sugar", "Karren Brady", "Deborah Meaden",
        "Peter Jones", "Theo Paphitis", "Duncan Bannatyne", "Sarah Willingham", "Nick Jenkins",
        "Oprah Winfrey", "Ellen DeGeneres", "Dr Phil", "Dr Oz", "Martha Stewart",
        "Rachael Ray", "Guy Fieri", "Anthony Bourdain", "Gordon Ramsay", "Wolfgang Puck",
        "Anna Wintour", "Karl Lagerfeld", "Donatella Versace", "Giorgio Armani", "Ralph Lauren",
        "Tommy Hilfiger", "Calvin Klein", "Vera Wang", "Diane von Furstenberg", "Michael Kors",
        "Victoria Beckham", "Stella McCartney", "Alexander McQueen", "Vivienne Westwood", "Burberry",
        "Pope Francis", "Dalai Lama", "Archbishop of Canterbury", "Joel Osteen", "T.D. Jakes",
        "Rick Warren", "Billy Graham", "Joyce Meyer", "Benny Hinn", "Kenneth Copeland",
        "Neil deGrasse Tyson", "Bill Nye", "Stephen Hawking", "Jane Goodall", "David Attenborough",
        "Brian Cox", "Michio Kaku", "Carl Sagan", "Richard Dawkins", "Sam Harris",
        "Malala Yousafzai", "Nelson Mandela", "Desmond Tutu", "Kofi Annan", "Ban Ki-moon",
        "Angela Merkel", "Emmanuel Macron", "Vladimir Putin", "Xi Jinping", "Justin Trudeau",
        "Jacinda Ardern", "Scott Morrison", "Narendra Modi", "Jair Bolsonaro", "Kim Jong-un"
    ],
    "tv_personalities": [
        "Graham Norton", "Holly Willoughby", "Ant McPartlin", "Declan Donnelly", "Phillip Schofield",
        "Jonathan Ross", "Alan Carr", "James Corden", "Piers Morgan", "Dermot O'Leary",
        "Claudia Winkleman", "Tess Daly", "Rylan Clark", "Gary Lineker", "David Attenborough",
        "Stephen Fry", "Oprah Winfrey", "Jimmy Fallon", "Jimmy Kimmel", "Stephen Colbert",
        "Trevor Noah", "Ryan Seacrest", "Carson Daly", "Simon Cowell", "Amanda Holden",
        "Lorraine Kelly", "Susanna Reid", "Kate Garraway", "Ben Shephard", "Davina McCall",
        "Fearne Cotton", "Keith Lemon", "Vernon Kay", "Alison Hammond", "Ruth Langsford",
        "Eamonn Holmes", "Christine Lampard", "Rochelle Humes", "Naga Munchetty", "Charlie Stayt",
        "Dan Walker", "Louise Minchin", "Bill Turnbull", "Sian Williams", "Victoria Derbyshire",
        "Andrew Marr", "Sophie Raworth", "Huw Edwards", "Fiona Bruce", "Emily Maitlis",
        "Kirsty Wark", "Jeremy Paxman", "David Dimbleby", "John Humphrys", "Mishal Husain",
        "Nick Robinson", "Laura Kuenssberg", "Robert Peston", "Krishnan Guru-Murthy", "Jon Snow",
        "Jeremy Clarkson", "James May", "Richard Hammond", "Chris Harris", "Paddy McGuinness",
        "Freddie Flintoff", "Matt LeBlanc", "Rory Reid", "Chris Evans", "Zoe Ball",
        "Sara Cox", "Jo Whiley", "Annie Mac", "Greg James", "Scott Mills",
        "Nick Grimshaw", "Clara Amfo", "Maya Jama", "Vick Hope", "Jordan North",
        "Roman Kemp", "Marvin Humes", "Myleene Klass", "Jamie Theakston", "Lucy Horobin",
        "Kelly Brook", "Amanda Byram", "Cat Deeley", "Tess Daly", "Alesha Dixon",
        "Bruno Tonioli", "Craig Revel Horwood", "Motsi Mabuse", "Shirley Ballas", "Darcey Bussell",
        "Len Goodman", "Anton Du Beke", "Oti Mabuse", "Giovanni Pernice", "Gorka Marquez",
        "Dianne Buswell", "Karen Hauer", "Janette Manrara", "Aljaz Skorjanec", "Pasha Kovalev",
        "Michael McIntyre", "Lee Mack", "Rob Brydon", "David Mitchell", "Jimmy Carr",
        "Sean Lock", "Jon Richardson", "Greg Davies", "Alex Horne", "Romesh Ranganathan",
        "Richard Ayoade", "Noel Fielding", "Matt Lucas", "David Walliams", "Russell Howard",
        "Jack Whitehall", "Kevin Hart", "Conan O'Brien", "Craig Ferguson", "James Corden"
    ],
    "other": [
        "Gordon Ramsay", "Bear Grylls", "Jeremy Clarkson", "Jamie Oliver", "Nigella Lawson",
        "Mary Berry", "Paul Hollywood", "Prue Leith", "Nadiya Hussain", "Ainsley Harriott",
        "Rick Stein", "Hugh Fearnley-Whittingstall", "Heston Blumenthal", "Marco Pierre White",
        "Delia Smith", "Nigel Slater", "Raymond Blanc", "Michel Roux Jr", "Tom Kerridge",
        "James Martin", "Gino D'Acampo", "Phil Vickery", "Aldo Zilli", "Antonio Carluccio",
        "Joe Wicks", "Davina McCall", "Mr Motivator", "Jane Fonda", "Richard Simmons",
        "David Lloyd", "Duncan Goodhew", "Sharron Davies", "Steve Backshall", "Ray Mears",
        "Bruce Parry", "Ben Fogle", "Levison Wood", "Simon Reeve", "Michael Palin",
        "Joanna Lumley", "Alan Whicker", "Judith Chalmers", "Anneka Rice", "Noel Edmonds",
        "Michael Barrymore", "Jim Davidson", "Bob Monkhouse", "Bruce Forsyth", "Des O'Connor",
        "Cilla Black", "Ronnie Corbett", "Ronnie Barker", "Tommy Cooper", "Morecambe and Wise",
        "The Two Ronnies", "Little and Large", "Cannon and Ball", "Mike Reid", "Jim Bowen",
        "Larry Grayson", "Hughie Green", "Bob Hope", "Danny Baker", "Chris Tarrant",
        "Anne Robinson", "Noel Edmonds", "Dale Winton", "Richard Whiteley", "Carol Vorderman",
        "Rachel Riley", "Susie Dent", "Nick Hewer", "Karren Brady", "Margaret Mountford",
        "Lord Sugar", "Peter Jones", "Deborah Meaden", "Theo Paphitis", "Duncan Bannatyne",
        "Sarah Willingham", "Touker Suleyman", "Sara Davies", "Steven Bartlett", "Gary Neville",
        "David Beckham", "Ryan Giggs", "Paul Scholes", "Roy Keane", "Gary Neville",
        "Jamie Carragher", "Steven Gerrard", "Frank Lampard", "John Terry", "Rio Ferdinand",
        "Michael Owen", "Alan Shearer", "Gary Lineker", "Ian Wright", "Chris Sutton",
        "Robbie Savage", "Jermaine Jenas", "Alex Scott", "Micah Richards", "Peter Crouch",
        "Judy Murray", "Tim Henman", "Sue Barker", "John McEnroe", "Martina Navratilova",
        "Boris Becker", "Steffi Graf", "Andre Agassi", "Pete Sampras", "Bjorn Borg",
        "David Ginola", "Eric Cantona", "Thierry Henry", "Patrick Vieira", "Dennis Bergkamp",
        "Arsene Wenger", "Alex Ferguson", "Jose Mourinho", "Pep Guardiola", "Jurgen Klopp"
    ]
}

async def fetch_wikipedia_info(name: str) -> dict:
    """Fetch celebrity info from Wikipedia API"""
    try:
        headers = {"User-Agent": "CelebrityBuzzIndex/1.0"}
        async with httpx.AsyncClient() as client:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{name.replace(' ', '_')}"
            response = await client.get(url, timeout=10.0, headers=headers)
            if response.status_code == 200:
                data = response.json()
                wiki_image = data.get("thumbnail", {}).get("source", "")
                return {
                    "name": data.get("title", name),
                    "bio": data.get("extract", "Celebrity profile"),
                    "image": wiki_image,
                    "wiki_url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
                }
    except Exception as e:
        print(f"  Error fetching {name}: {e}")
    return {"name": name, "bio": "Celebrity profile", "image": "", "wiki_url": ""}

async def populate_category(db, category: str, target: int = 200):
    """Populate a category to reach target count"""
    pool = EXTENDED_POOLS.get(category, [])
    if not pool:
        print(f"No pool for {category}")
        return
    
    current_count = await db.celebrities.count_documents({"category": category})
    needed = target - current_count
    
    print(f"\n{category}: {current_count}/{target} (need {needed} more)")
    
    if needed <= 0:
        print(f"  Already at target!")
        return
    
    # Get existing names to avoid duplicates
    existing = await db.celebrities.find({"category": category}, {"name": 1}).to_list(1000)
    existing_names = {c["name"].lower() for c in existing}
    
    added = 0
    for name in pool:
        if added >= needed:
            break
        if name.lower() in existing_names:
            continue
        
        # Check if exists in any category
        exists = await db.celebrities.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
        if exists:
            continue
        
        # Fetch from Wikipedia
        wiki_info = await fetch_wikipedia_info(name)
        
        # Create placeholder if no image
        image = wiki_info.get("image", "")
        if not image:
            clean_name = name.replace(' ', '+')
            image = f"https://ui-avatars.com/api/?name={clean_name}&size=400&background=1a1a1a&color=FF0099&bold=true&format=png"
        
        # Create celebrity document
        doc = {
            "id": str(uuid.uuid4()),
            "name": wiki_info.get("name", name),
            "bio": wiki_info.get("bio", "Celebrity profile")[:500],
            "image": image,
            "category": category,
            "wiki_url": wiki_info.get("wiki_url", ""),
            "buzz_score": 50,
            "price": 5.0,
            "tier": "C",
            "news": [],
            "is_deceased": False,
            "birth_year": 0,
            "age": 0,
            "times_picked": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.celebrities.insert_one(doc)
        existing_names.add(name.lower())
        added += 1
        
        if added % 10 == 0:
            print(f"  Added {added}/{needed}...")
    
    print(f"  Completed: Added {added} celebrities to {category}")

async def main():
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    db = client[os.environ.get("DB_NAME", "test_database")]
    
    print("=" * 50)
    print("POPULATING DATABASE TO 200 PER CATEGORY")
    print("=" * 50)
    
    for category in EXTENDED_POOLS.keys():
        await populate_category(db, category, 200)
    
    # Final counts
    print("\n" + "=" * 50)
    print("FINAL COUNTS")
    print("=" * 50)
    
    for category in EXTENDED_POOLS.keys():
        count = await db.celebrities.count_documents({"category": category})
        status = "✓" if count >= 200 else f"({count}/200)"
        print(f"{category}: {count} {status}")
    
    total = await db.celebrities.count_documents({})
    print(f"\nTotal celebrities: {total}")

if __name__ == "__main__":
    asyncio.run(main())

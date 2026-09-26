// Present a POSIX-looking cwd (drive letter dropped; the tool runs on the same drive).
const c = process.cwd.bind(process);
process.cwd = () => c().replace(/^[A-Za-z]:/, '').split('\\').join('/');
